from __future__ import annotations

import asyncio
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from adtech_agents.agents.max_chat_agent import build_max_chat_agent
from adtech_agents.config import Config
from adtech_agents.context import Context
from adtech_agents.github_app import GitHubError
from adtech_agents.reference_data import ReferenceData, load_reference_data
from adtech_agents.schemas import AuditReport
from adtech_agents.tools import chat_tools
from adtech_agents.tools.chat_tools import ChatState, audit_project, install
from adtech_agents.tools.common import ToolError
from adtech_agents.workflows.install_pods_workflow import InstallResult
from tests.conftest import FIXTURES, REFERENCE_DATA

PROJECT = FIXTURES / "ios_swift_max_network_missing_admob"
GITHUB_URL = "https://github.com/acme/puzzle"
SNAPSHOT = load_reference_data(REFERENCE_DATA)
GOOGLE_POD = "AppLovinMediationGoogleAdapter"


@dataclass
class Calls:
    audited: list[Path] = field(default_factory=list)
    installed: list[tuple[str, list[str]]] = field(default_factory=list)
    closed: int = 0


@pytest.fixture
def ctx() -> Iterator[Context]:
    ctx = Context.create(Config())
    yield ctx
    ctx.shutdown()


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> Calls:
    """
    Replace the audit, the clone and the pull request, which call the model and GitHub.
    """
    calls = Calls()

    async def fake_audit(root: Path, ctx: Context, reference: ReferenceData) -> AuditReport:
        assert reference is SNAPSHOT
        calls.audited.append(root)
        return AuditReport(summary="One adapter is missing.", findings=[], rejected_findings=[])

    @dataclass
    class FakeWorkspace:
        root: Path = PROJECT
        base: str = "main"

        def close(self) -> None:
            calls.closed += 1

    def fake_install(
        source: str, pods: list[str], ctx: Context, reference: ReferenceData
    ) -> InstallResult:
        assert reference is SNAPSHOT
        calls.installed.append((source, pods))
        return InstallResult(pull_request_url=f"{source}/pull/1", diff="+  pod ...")

    monkeypatch.setattr(chat_tools, "audit_max_integration", fake_audit)
    monkeypatch.setattr(chat_tools, "open_workspace", lambda *args: FakeWorkspace())
    monkeypatch.setattr(chat_tools, "install_pods", fake_install)
    return calls


def _state(ctx: Context, allow_local_paths: bool = True) -> ChatState:
    return ChatState(ctx=ctx, allow_local_paths=allow_local_paths, reference=SNAPSHOT)


def test_audit_then_install_a_local_project(ctx: Context, calls: Calls) -> None:
    state = _state(ctx)
    result = asyncio.run(audit_project(state, f" {PROJECT} "))
    assert calls.audited == [PROJECT]
    assert "local checkout" in result.note

    installed = asyncio.run(install(state, [GOOGLE_POD]))
    assert calls.installed == [(str(PROJECT), [GOOGLE_POD])]
    assert installed.pull_request_url == f"{PROJECT}/pull/1"


def test_audit_a_github_url_in_a_temporary_clone(ctx: Context, calls: Calls) -> None:
    state = _state(ctx, allow_local_paths=False)
    result = asyncio.run(audit_project(state, GITHUB_URL))
    assert calls.audited == [PROJECT]
    assert calls.closed == 1
    assert result.note == "Audited the main branch on GitHub."
    assert state.source == GITHUB_URL


def test_local_paths_are_refused_when_not_allowed(ctx: Context, calls: Calls) -> None:
    state = _state(ctx, allow_local_paths=False)
    with pytest.raises(ToolError, match="only GitHub repository URLs"):
        asyncio.run(audit_project(state, str(PROJECT)))
    assert calls.audited == []
    assert state.source is None


def test_unknown_source_is_refused(ctx: Context, calls: Calls) -> None:
    with pytest.raises(ToolError, match="neither a local directory nor a GitHub"):
        asyncio.run(audit_project(_state(ctx), "https://gitlab.com/acme/puzzle"))


def test_install_needs_an_audited_project(ctx: Context, calls: Calls) -> None:
    with pytest.raises(ToolError, match="audit a project"):
        asyncio.run(install(_state(ctx), [GOOGLE_POD]))
    assert calls.installed == []


def test_github_failures_reach_the_model(
    ctx: Context, calls: Calls, monkeypatch: pytest.MonkeyPatch
) -> None:
    def not_installed(*args: object) -> None:
        raise GitHubError("the GitHub App is not installed on acme/puzzle")

    monkeypatch.setattr(chat_tools, "open_workspace", not_installed)
    with pytest.raises(ToolError, match="not installed on acme/puzzle"):
        asyncio.run(audit_project(_state(ctx), GITHUB_URL))


@pytest.mark.parametrize("allow_local_paths", [True, False])
def test_chat_agent_lists_supported_pods(allow_local_paths: bool) -> None:
    agent = build_max_chat_agent(allow_local_paths)
    assert [tool.name for tool in agent.tools] == ["audit_project", "install_pods"]
    assert isinstance(agent.instructions, str)
    assert f"- {GOOGLE_POD}\n" in agent.instructions
    assert ("local directory path" in agent.instructions) is allow_local_paths

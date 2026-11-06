"""
Tools of the chat agent: audit a publisher's project with the iOS MAX Audit Agent, then install
pods in it through a pull request. Our code clones, audits and edits; the model only relays the
project the publisher named and chooses pods.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel

from adtech_agents.context import Context
from adtech_agents.github_app import GitHubApp, GitHubError, parse_github_url
from adtech_agents.project_changes import ChangeError
from adtech_agents.reference_data import ReferenceData, ReferenceDataError, fetch_reference_data
from adtech_agents.schemas import AuditReport, Finding
from adtech_agents.tools.common import ToolError, tool_error
from adtech_agents.tools.inspect_app_project import UnsupportedProjectError
from adtech_agents.workflows.audit_max_integration_workflow import audit_max_integration
from adtech_agents.workflows.install_pods_workflow import InstallResult, install_pods
from adtech_agents.workspace import WorkspaceError, open_workspace

Progress = Literal["auditing", "opening_pull_request"]


@dataclass
class ChatState:
    """
    Per-conversation state handed to every chat tool.
    """

    ctx: Context
    allow_local_paths: bool
    """
    Whether the publisher may name a directory on this machine (terminal), or only GitHub URLs
    (Slack, where the machine is not theirs).
    """
    source: str | None = None
    """
    The project audited last; `install_pods` changes only this one.
    """
    reference: ReferenceData | None = None
    """
    Fetched once per conversation, so the audit and the pull request agree on versions.
    """
    on_progress: Callable[[Progress, str], Awaitable[None]] | None = None
    """
    Called when slow work starts, with the step and the project, so the interface can show it.
    """

    async def report(self, step: Progress, source: str) -> None:
        if self.on_progress is not None:
            await self.on_progress(step, source)


class AuditResult(BaseModel):
    source: str
    note: str
    summary: str
    findings: list[Finding]


@function_tool(name_override="audit_project", failure_error_function=tool_error)
async def audit_project_tool(ctx: RunContextWrapper[ChatState], source: str) -> str:
    """
    Audit the AppLovin MAX integration of an iOS project. Returns a summary and findings with
    file and line evidence.

    Args:
        source: The project exactly as the publisher gave it: a GitHub repository URL, or a local
            directory path when local paths are allowed.
    """
    return (await audit_project(ctx.context, source)).model_dump_json()


@function_tool(name_override="install_pods", failure_error_function=tool_error)
async def install_pods_tool(ctx: RunContextWrapper[ChatState], pods: list[str]) -> str:
    """
    Add or update pods in the audited project's Podfile at their newest versions and open a
    GitHub pull request. Adding the AdMob adapter also adds a placeholder AdMob app ID to the
    app's Info.plist. Returns the pull request URL (null if nothing needed changing) and the diff.

    Args:
        pods: Pod names from the supported list in your instructions, all in one call.
    """
    return (await install(ctx.context, pods)).model_dump_json()


async def audit_project(state: ChatState, source: str) -> AuditResult:
    source = source.strip()
    local = Path(source).expanduser()
    with _as_tool_errors():
        if parse_github_url(source) is not None:
            await state.report("auditing", source)
            reference = await _reference_data(state)
            report, note = await _audit_github(state, source, reference)
        elif state.allow_local_paths and local.is_dir():
            await state.report("auditing", source)
            reference = await _reference_data(state)
            report = await audit_max_integration(local, state.ctx, reference)
            note = (
                "Audited the local checkout, including uncommitted changes. Pull requests start "
                "from the GitHub default branch."
            )
        elif state.allow_local_paths:
            raise ToolError(f"{source} is neither a local directory nor a GitHub repository URL")
        else:
            raise ToolError("only GitHub repository URLs are accepted, e.g. https://github.com/o/r")
    state.source = source
    return AuditResult(source=source, note=note, summary=report.summary, findings=report.findings)


async def install(state: ChatState, pods: list[str]) -> InstallResult:
    if state.source is None:
        raise ToolError("audit a project with audit_project first")
    if not pods:
        raise ToolError("name at least one pod")
    await state.report("opening_pull_request", state.source)
    with _as_tool_errors():
        reference = await _reference_data(state)
        return await asyncio.to_thread(install_pods, state.source, pods, state.ctx, reference)


async def _audit_github(
    state: ChatState, source: str, reference: ReferenceData
) -> tuple[AuditReport, str]:
    """
    Audit a temporary clone of the default branch (through the GitHub App, so private
    repositories work too).
    """
    config = state.ctx.config
    workspace = await asyncio.to_thread(open_workspace, source, GitHubApp(config), config)
    try:
        report = await audit_max_integration(workspace.root, state.ctx, reference)
    finally:
        workspace.close()
    return report, f"Audited the {workspace.base} branch on GitHub."


async def _reference_data(state: ChatState) -> ReferenceData:
    if state.reference is None:
        state.reference = await asyncio.to_thread(fetch_reference_data, state.ctx.config)
    return state.reference


@contextmanager
def _as_tool_errors() -> Iterator[None]:
    """
    Project and GitHub setup failures become messages the model can relay to the publisher.
    """
    try:
        yield
    except (
        UnsupportedProjectError,
        ReferenceDataError,
        GitHubError,
        WorkspaceError,
        ChangeError,
    ) as exc:
        raise ToolError(str(exc)) from exc

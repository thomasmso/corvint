from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from adtech_agents import build_check
from adtech_agents.build_check import build_project
from adtech_agents.config import Config
from tests.conftest import FIXTURES

CONFIG = Config()


@pytest.fixture
def app(tmp_path: Path) -> Path:
    root = tmp_path / "app"
    shutil.copytree(FIXTURES / "ios_swift_max_clean", root)
    return root


class FakeTools:
    """
    Stands in for `pod` and `xcodebuild`; records each command and the environment it got.
    """

    def __init__(self, fail: str | None = None, schemes: list[str] | None = None) -> None:
        self.fail = fail
        self.schemes = schemes if schemes is not None else ["PuzzleQuest"]
        self.commands: list[list[str]] = []
        self.envs: list[dict[str, str]] = []

    def run(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        self.envs.append(kwargs["env"])
        cwd = Path(kwargs.get("cwd") or ".")
        if command[:2] == ["pod", "install"] and self.fail != "pod":
            (cwd / "PuzzleQuest.xcworkspace").mkdir()
        if command[:2] == ["xcodebuild", "-list"]:
            out = json.dumps({"project": {"schemes": self.schemes}})
            return subprocess.CompletedProcess(command, 0, out, "")
        if command[:2] == ["xcodebuild", "-version"]:
            return subprocess.CompletedProcess(command, 0, "Xcode 27.2\nBuild version 27B52\n", "")
        failed = (self.fail == "pod" and command[0] == "pod") or (
            self.fail == "build" and command[:2] == ["xcodebuild", "build"]
        )
        if failed:
            log = "\n".join(f"line {n}" for n in range(1, 41)) + "\nerror: no such module"
            return subprocess.CompletedProcess(command, 1, log, "")
        return subprocess.CompletedProcess(command, 0, "", "")


@pytest.fixture
def tools(monkeypatch: pytest.MonkeyPatch) -> FakeTools:
    fake = FakeTools()
    monkeypatch.setattr(build_check.shutil, "which", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(build_check.subprocess, "run", fake.run)
    return fake


def test_installs_pods_then_builds_the_only_scheme_for_the_simulator(
    app: Path, tools: FakeTools
) -> None:
    steps: list[str] = []
    result = build_project(app, CONFIG, steps.append)
    assert steps == ["installing_pods", "compiling"]
    assert result.status == "succeeded"
    assert "scheme PuzzleQuest" in result.summary
    assert "Xcode 27.2" in result.summary
    assert tools.commands[0] == ["pod", "install"]
    build = next(c for c in tools.commands if c[:2] == ["xcodebuild", "build"])
    assert build[build.index("-workspace") + 1] == "PuzzleQuest.xcworkspace"
    assert build[build.index("-destination") + 1] == "generic/platform=iOS Simulator"
    assert "CODE_SIGNING_ALLOWED=NO" in build


def test_build_gets_no_credentials(
    app: Path, tools: FakeTools, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", "/keys/app.pem")
    build_project(app, CONFIG)
    for env in tools.envs:
        assert "OPENAI_API_KEY" not in env
        assert "GITHUB_APP_PRIVATE_KEY_PATH" not in env
        assert "PATH" in env


@pytest.mark.parametrize(
    ("fail", "summary"), [("pod", "`pod install` failed."), ("build", "Build failed")]
)
def test_failures_keep_the_end_of_the_log(
    app: Path, tools: FakeTools, fail: str, summary: str
) -> None:
    tools.fail = fail
    result = build_project(app, CONFIG)
    assert result.status == "failed"
    assert result.summary.startswith(summary)
    assert result.log_tail == "error: no such module"


def test_log_excerpt_prefers_distinct_errors_and_cuts_long_lines() -> None:
    compiler = "swift-frontend " + "-flag " * 200
    error = "/private/var/folders/x/app/a.swift:3: error: x"
    output = f"{compiler}\n{error}\n{compiler}\n{error}\n** BUILD FAILED **"
    cwd = Path("/private/var/folders/x/app")
    assert build_check._excerpt(output, cwd) == "a.swift:3: error: x"
    tail = build_check._excerpt(f"{compiler}\n** BUILD FAILED **", cwd).splitlines()
    assert tail[0].endswith("…") and len(tail[0]) == 301
    assert tail[1] == "** BUILD FAILED **"


def test_several_schemes_are_not_guessed(app: Path, tools: FakeTools) -> None:
    tools.schemes = ["PuzzleQuest", "PuzzleQuestTests"]
    result = build_project(app, CONFIG)
    assert result.status == "skipped"
    assert "exactly one scheme" in result.summary
    assert not any(c[:2] == ["xcodebuild", "build"] for c in tools.commands)


def test_skipped_without_xcode(app: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        build_check.shutil, "which", lambda tool: None if tool == "xcodebuild" else "/bin/pod"
    )
    result = build_project(app, CONFIG)
    assert result.status == "skipped"
    assert result.summary == "Not built: xcodebuild not found on this machine."


def test_skipped_without_exactly_one_project(app: Path, tools: FakeTools) -> None:
    shutil.copytree(app / "PuzzleQuest.xcodeproj", app / "Other.xcodeproj")
    result = build_project(app, CONFIG)
    assert result.status == "skipped"
    assert tools.commands == []

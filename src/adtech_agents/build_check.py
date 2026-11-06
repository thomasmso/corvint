"""
Build check for a changed copy: `pod install`, then `xcodebuild` for the iOS Simulator with code
signing off. Our code runs these fixed commands in the temporary copy; the model never does.

Both commands run the repository's own code (a Podfile is Ruby, build phases are scripts), so they
get a minimal environment without our credentials. They run only on projects the publisher named:
a local path typed in the terminal, or a repository the GitHub App is installed on.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from adtech_agents.config import Config

BuildStep = Literal["installing_pods", "compiling"]

# Passed to the build; everything else (API keys, GitHub App settings) is left out.
_ENV_KEYS = ("PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL", "DEVELOPER_DIR")
_LOG_TAIL_LINES = 30
_LOG_LINE_CHARS = 300


class BuildResult(BaseModel):
    status: Literal["succeeded", "failed", "skipped"]
    summary: str
    """
    One sentence for the publisher and the pull request, e.g. which scheme was built.
    """
    log_tail: str = ""
    """
    The failing command's error lines (or its last lines); empty unless `status` is "failed".
    """


def build_project(
    podfile_dir: Path, config: Config, on_step: Callable[[BuildStep], None] | None = None
) -> BuildResult:
    """
    Install pods and build the app in `podfile_dir` (the directory holding the only Podfile).
    `on_step` is called as each command starts.
    """
    report = on_step or (lambda step: None)
    missing = [tool for tool in ("pod", "xcodebuild") if shutil.which(tool) is None]
    if missing:
        tools = " and ".join(missing)
        return BuildResult(
            status="skipped", summary=f"Not built: {tools} not found on this machine."
        )
    projects = sorted(p.name for p in podfile_dir.glob("*.xcodeproj"))
    if len(projects) != 1:
        found = len(projects)
        return BuildResult(
            status="skipped",
            summary=f"Not built: expected one .xcodeproj next to the Podfile, found {found}.",
        )

    report("installing_pods")
    failure = _run(["pod", "install"], podfile_dir, config)
    if failure is not None:
        return BuildResult(status="failed", summary="`pod install` failed.", log_tail=failure)

    workspace = Path(projects[0]).with_suffix(".xcworkspace").name
    if not (podfile_dir / workspace).is_dir():
        return BuildResult(status="failed", summary=f"`pod install` did not create {workspace}.")
    scheme = _app_scheme(podfile_dir / projects[0], config)
    if scheme is None:
        return BuildResult(
            status="skipped",
            summary=f"Not built: {projects[0]} does not have exactly one scheme to build.",
        )

    command = [
        "xcodebuild",
        "build",
        "-workspace",
        workspace,
        "-scheme",
        scheme,
        "-destination",
        config.BUILD_DESTINATION,
        "-derivedDataPath",
        str(podfile_dir / "build" / "DerivedData"),
        "-quiet",
        "CODE_SIGNING_ALLOWED=NO",
    ]
    where = f"scheme {scheme} for {config.BUILD_DESTINATION}, {_xcode_version(config)}"
    report("compiling")
    failure = _run(command, podfile_dir, config)
    if failure is not None:
        return BuildResult(status="failed", summary=f"Build failed ({where}).", log_tail=failure)
    return BuildResult(status="succeeded", summary=f"Built after `pod install` ({where}).")


def _app_scheme(project: Path, config: Config) -> str | None:
    """
    The project's only scheme, or `None` when there are none or several (ambiguous).
    """
    try:
        result = subprocess.run(
            ["xcodebuild", "-list", "-json", "-project", project.name],
            cwd=project.parent,
            env=_build_env(),
            capture_output=True,
            text=True,
            timeout=config.BUILD_TIMEOUT_SECONDS,
        )
        schemes = json.loads(result.stdout)["project"]["schemes"]
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
        return None
    return str(schemes[0]) if isinstance(schemes, list) and len(schemes) == 1 else None


def _xcode_version(config: Config) -> str:
    try:
        result = subprocess.run(
            ["xcodebuild", "-version"],
            env=_build_env(),
            capture_output=True,
            text=True,
            timeout=config.BUILD_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown Xcode"
    return result.stdout.splitlines()[0] if result.stdout else "unknown Xcode"


def _run(command: list[str], cwd: Path, config: Config) -> str | None:
    """
    `None` on success, else an excerpt of the output.
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=_build_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=config.BUILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"{command[0]} timed out after {config.BUILD_TIMEOUT_SECONDS:.0f} s"
    except OSError as exc:
        return f"{command[0]} could not start: {exc}"
    if result.returncode == 0:
        return None
    return _excerpt(result.stdout + result.stderr, cwd)


def _excerpt(output: str, cwd: Path) -> str:
    """
    The distinct `error:` lines, or else the last lines, with paths relative to `cwd`; long lines
    (compiler invocations run to thousands of characters) are cut.
    """
    # Xcode prints /tmp and /var paths without the /private that resolve() adds on macOS
    for prefix in {str(cwd), str(cwd).removeprefix("/private")}:
        output = output.replace(prefix + "/", "")
    lines = output.strip().splitlines()
    errors = list(dict.fromkeys(line.strip() for line in lines if "error:" in line))
    chosen = errors[:_LOG_TAIL_LINES] if errors else lines[-_LOG_TAIL_LINES:]
    return "\n".join(
        line if len(line) <= _LOG_LINE_CHARS else line[:_LOG_LINE_CHARS] + "…" for line in chosen
    )


def _build_env() -> dict[str, str]:
    env = {key: os.environ[key] for key in _ENV_KEYS if key in os.environ}
    # CocoaPods prints a warning and may fail without a UTF-8 locale
    env.setdefault("LANG", "en_US.UTF-8")
    return env

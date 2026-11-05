"""
Project inspection for iOS apps: Podfiles and their AppLovin MAX CocoaPods dependencies.

Versions are the constraints exactly as written in the `Podfile` and never inferred.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from agents import RunContextWrapper, function_tool

from adtech_agents.config import Config
from adtech_agents.schemas import Dependency, RepositoryInfo
from adtech_agents.tools.code_search import iter_files, read_text
from adtech_agents.tools.common import AuditContext, tool_error

UNITY_PROJECT_MARKER = "ProjectSettings/ProjectVersion.txt"

_POD_RE = re.compile(r"""^\s*pod\s+['"]([^'"]+)['"](.*)$""")
_POD_VERSION_RE = re.compile(r""",\s*['"]([^'"]+)['"]""")


class UnsupportedProjectError(Exception):
    """
    The project cannot be audited reliably, so the run stops before the model is called.
    """


# Entry point for OAI SDK tool calling. The docstring is the tool description the model sees.
@function_tool(name_override="inspect_app_project", failure_error_function=tool_error)
def inspect_app_project_tool(ctx: RunContextWrapper[AuditContext]) -> str:
    """
    Detected platform, Podfile paths and AppLovin pods (version constraints exactly as
    written). Call this first.
    """
    return ctx.context.repository_info.model_dump_json()


def inspect_app_project(root: Path, config: Config) -> RepositoryInfo:
    """
    Inspect an iOS app project and return a RepositoryInfo object. May break with Flutter, etc.
    """
    files: list[str] = []
    for file in iter_files(root):  # iter_files filter out Pods/ and build output, etc
        if len(files) == config.MAX_FILES:
            raise UnsupportedProjectError(
                f"{root} has more than {config.MAX_FILES} files (excluding build output)"
            )
        files.append(file)

    # Unity projects are not supported in V1
    if UNITY_PROJECT_MARKER in files:
        raise UnsupportedProjectError(f"{root} is a Unity project; only native iOS is supported")

    # Grab Podfile dependencies
    dependency_files: list[str] = []
    dependencies: list[Dependency] = []
    for file in files:
        if PurePosixPath(file).name == "Podfile":  # Support Podfile for now, SPM later
            dependency_files.append(file)
            current_dependencies = _parse_podfile(file, read_text(root / file) or "")
            dependencies.extend(current_dependencies)

    is_ios = bool(dependency_files) or any(".xcodeproj/" in file for file in files)
    if not is_ios:
        raise UnsupportedProjectError(f"{root} is not an iOS project")

    return RepositoryInfo(
        project=root.name,
        platform="ios" if is_ios else "unknown",
        dependency_files=dependency_files,
        dependencies=dependencies,
    )


def _parse_podfile(file: str, content: str) -> list[Dependency]:
    deps = []
    for number, line in enumerate(content.splitlines(), start=1):
        match = _POD_RE.match(line.split("#", 1)[0])
        if not match or not match.group(1).startswith("AppLovin"):
            continue

        # Parse out the AppLovin SDK or adapter version constraint
        # (e.g. '13.6.4', '~> 13.6', '>= 13.6.4', '')
        constraints = _POD_VERSION_RE.findall(match.group(2))
        deps.append(
            Dependency(
                name=match.group(1),  # e.g. 'AppLovinSDK', 'AppLovinMediationUnityAdsAdapter'
                version=", ".join(constraints) or None,
                source_file=file,
                line=number,
            )
        )

    return deps

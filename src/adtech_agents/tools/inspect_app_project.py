"""
Project inspection for iOS apps: Podfiles and their AppLovin MAX CocoaPods dependencies, and
the AppLovin-relevant keys of each `Info.plist`.

Versions are the constraints exactly as written in the `Podfile` and never inferred. The newest
SDK version and AppLovin's SKAdNetwork IDs come from `ReferenceData`, not from the repository.
"""

from __future__ import annotations

import plistlib
import re
from pathlib import Path, PurePosixPath
from typing import Any

from agents import RunContextWrapper, function_tool

from adtech_agents.config import Config
from adtech_agents.reference_data import ReferenceData, version_key
from adtech_agents.schemas import Dependency, InfoPlist, RepositoryInfo
from adtech_agents.tools.code_search import iter_files, read_text
from adtech_agents.tools.common import AuditContext, tool_error

UNITY_PROJECT_MARKER = "ProjectSettings/ProjectVersion.txt"
SDK_POD = "AppLovinSDK"

_POD_RE = re.compile(r"""^\s*pod\s+['"]([^'"]+)['"](.*)$""")
_POD_VERSION_RE = re.compile(r""",\s*['"]([^'"]+)['"]""")
_CONSTRAINT_RE = re.compile(r"^(~>|>=|<=|!=|=|>|<)?\s*(\d+(?:\.\d+)*)$")


class UnsupportedProjectError(Exception):
    """
    The project cannot be audited reliably, so the run stops before the model is called.
    """


# Entry point for OAI SDK tool calling. The docstring is the tool description the model sees.
@function_tool(name_override="inspect_app_project", failure_error_function=tool_error)
def inspect_app_project_tool(ctx: RunContextWrapper[AuditContext]) -> str:
    """
    Detected platform; Podfile paths and AppLovin pods (version constraints exactly as written,
    and for AppLovinSDK whether the constraint allows latest_sdk_version); and per Info.plist
    whether AppLovinSdkKey and NSUserTrackingUsageDescription are set, how many SKAdNetwork IDs
    it lists and which of AppLovin's are missing. Call this first.
    """
    return ctx.context.repository_info.model_dump_json()


def inspect_app_project(root: Path, config: Config, reference: ReferenceData) -> RepositoryInfo:
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
    info_plists: list[InfoPlist] = []
    for file in files:
        name = PurePosixPath(file).name
        if name == "Podfile":  # Support Podfile for now, SPM later
            dependency_files.append(file)
            content = read_text(root / file) or ""
            dependencies.extend(_parse_podfile(file, content, reference.latest_sdk_version))
        elif name == "Info.plist":
            info_plist = _parse_info_plist(root, file, reference.skadnetwork_ids)
            if info_plist is not None:
                info_plists.append(info_plist)

    is_ios = bool(dependency_files) or any(".xcodeproj/" in file for file in files)
    if not is_ios:
        raise UnsupportedProjectError(f"{root} is not an iOS project")

    return RepositoryInfo(
        platform="ios" if is_ios else "unknown",
        dependency_files=dependency_files,
        dependencies=dependencies,
        info_plists=info_plists,
        latest_sdk_version=reference.latest_sdk_version,
    )


def _parse_podfile(file: str, content: str, latest_sdk_version: str) -> list[Dependency]:
    deps = []
    for number, line in enumerate(content.splitlines(), start=1):
        match = _POD_RE.match(line.split("#", 1)[0])
        if not match or not match.group(1).startswith("AppLovin"):
            continue

        # Parse out the AppLovin SDK or adapter version constraint
        # (e.g. '13.6.4', '~> 13.6', '>= 13.6.4', '')
        name = match.group(1)  # e.g. 'AppLovinSDK', 'AppLovinMediationUnityAdsAdapter'
        constraints = _POD_VERSION_RE.findall(match.group(2))
        deps.append(
            Dependency(
                name=name,
                version=", ".join(constraints) or None,
                source_file=file,
                line=number,
                allows_latest_version=(
                    allows_version(constraints, latest_sdk_version) if name == SDK_POD else None
                ),
            )
        )

    return deps


def allows_version(constraints: list[str], version: str) -> bool | None:
    """
    Whether CocoaPods constraints such as `["~> 13.6"]` admit `version`; `None` if any
    constraint cannot be parsed. No constraint admits every version.
    """
    target = version_key(version)
    for constraint in constraints:
        match = _CONSTRAINT_RE.match(constraint.strip())
        if not match:
            return None
        operator, bound = match.group(1) or "=", version_key(match.group(2))
        if not _satisfies(target, operator, bound):
            return False
    return True


def _satisfies(version: tuple[int, ...], operator: str, bound: tuple[int, ...]) -> bool:
    # Pad with zeros so 13.6 == 13.6.0
    width = max(len(version), len(bound))
    v, b = version + (0,) * (width - len(version)), bound + (0,) * (width - len(bound))
    match operator:
        case "=":
            return v == b
        case "!=":
            return v != b
        case ">":
            return v > b
        case "<":
            return v < b
        case ">=":
            return v >= b
        case "<=":
            return v <= b
        case _:  # "~> 13.6" means >= 13.6 and < 14; "~> 13.6.4" means >= 13.6.4 and < 13.7
            upper = (*bound[:-2], bound[-2] + 1) if len(bound) > 1 else (bound[0] + 1,)
            upper += (0,) * (width - len(upper))
            return b <= v < upper


def _parse_info_plist(root: Path, file: str, applovin_ids: list[str]) -> InfoPlist | None:
    """
    `None` for unreadable or non-dictionary plists.
    """
    try:
        data: Any = plistlib.loads((root / file).read_bytes())
    except (OSError, plistlib.InvalidFileException, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    listed: set[str] = set()
    for item in data.get("SKAdNetworkItems") or []:
        if isinstance(item, dict) and isinstance(item.get("SKAdNetworkIdentifier"), str):
            listed.add(item["SKAdNetworkIdentifier"].lower())

    return InfoPlist(
        path=file,
        sdk_key_present=bool(data.get("AppLovinSdkKey")),
        tracking_usage_description_present=bool(data.get("NSUserTrackingUsageDescription")),
        skadnetwork_id_count=len(listed),
        missing_applovin_skadnetwork_ids=[i for i in applovin_ids if i not in listed],
    )

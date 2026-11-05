"""
Edits to a publisher's project for installing MAX pods, written by our code (the model only picks
which pods): `pod` lines in the Podfile, with versions from `ReferenceData` only, and the AdMob app
ID placeholder in the app's Info.plist. Changes are planned first, so they can be shown as a diff,
then applied.
"""

from __future__ import annotations

import difflib
import plistlib
import re
from pathlib import Path, PurePosixPath
from typing import Any
from xml.sax.saxutils import escape

from pydantic import BaseModel

from adtech_agents.config import Config
from adtech_agents.reference_data import ADAPTER_PODS, ReferenceData
from adtech_agents.tools.code_search import iter_files, read_text, resolve_repo_file
from adtech_agents.tools.common import ToolError
from adtech_agents.tools.inspect_app_project import (
    POD_RE,
    POD_VERSION_RE,
    SDK_POD,
    allows_version,
)

ADMOB_ADAPTER_POD = ADAPTER_PODS["ADMOB_NETWORK"]
ADMOB_APP_ID_KEY = "GADApplicationIdentifier"

_PLIST_KEY_INDENT_RE = re.compile(r"^([ \t]*)<key>", re.MULTILINE)


class ChangeError(Exception):
    """
    The change cannot be made safely, so nothing is written.
    """


class FileChange(BaseModel):
    path: str
    """
    Repository-relative path.
    """
    old: str
    new: str

    def diff(self) -> str:
        return "".join(
            difflib.unified_diff(
                self.old.splitlines(keepends=True),
                self.new.splitlines(keepends=True),
                f"a/{self.path}",
                f"b/{self.path}",
            )
        )


def plan_pod_changes(
    root: Path, pods: list[str], reference: ReferenceData, config: Config
) -> list[FileChange]:
    """
    Changes that make the Podfile declare each of `pods` (AppLovinSDK or an `ADAPTER_PODS`
    adapter) with a constraint that allows its newest version, and, with the AdMob adapter, give
    the app's Info.plist an AdMob app ID placeholder if it has none. Pods whose constraint already
    allows the newest version are left alone, so an empty list means nothing to change.
    """
    newest = {SDK_POD: reference.latest_sdk_version, **reference.adapter_versions}
    unknown = [pod for pod in pods if pod not in newest]
    if unknown:
        raise ChangeError(f"cannot install {', '.join(unknown)}; supported: {', '.join(newest)}")

    files = list(iter_files(root))
    podfile = _podfile(files)
    changes = []
    old = _read(root, podfile)
    new = _set_pod_versions(old, {pod: newest[pod] for pod in pods})
    if new != old:
        changes.append(FileChange(path=podfile, old=old, new=new))

    if ADMOB_ADAPTER_POD in pods:
        plist = _app_info_plist(root, files)
        old = _read(root, plist)
        if ADMOB_APP_ID_KEY not in _load_plist(old, plist):
            new = _add_plist_string(old, plist, ADMOB_APP_ID_KEY, config.ADMOB_APP_ID_PLACEHOLDER)
            changes.append(FileChange(path=plist, old=old, new=new))
    return changes


def apply_changes(root: Path, changes: list[FileChange]) -> None:
    """
    Write planned changes, refusing all of them if any file changed since it was planned.
    """
    paths = []
    for change in changes:
        try:
            path = resolve_repo_file(change.path, root)
        except ToolError as exc:
            raise ChangeError(str(exc)) from exc
        if read_text(path) != change.old:
            raise ChangeError(f"{change.path} changed since the change was planned")
        paths.append(path)
    for path, change in zip(paths, changes, strict=True):
        path.write_text(change.new, encoding="utf-8")


def _podfile(files: list[str]) -> str:
    podfiles = [file for file in files if PurePosixPath(file).name == "Podfile"]
    if len(podfiles) != 1:
        raise ChangeError(f"expected exactly one Podfile, found {podfiles}")
    return podfiles[0]


def _read(root: Path, rel: str) -> str:
    text = read_text(root / rel)
    if text is None or "\ufffd" in text:
        raise ChangeError(f"{rel} is not a UTF-8 text file")
    return text


def _set_pod_versions(text: str, versions: dict[str, str]) -> str:
    lines = text.splitlines(keepends=True)
    declared: dict[str, list[int]] = {}
    for index, line in enumerate(lines):
        match = POD_RE.match(line.split("#", 1)[0])
        if match:
            declared.setdefault(match.group(1), []).append(index)

    to_add = []
    for pod, version in versions.items():
        at = declared.get(pod, [])
        if len(at) > 1:
            raise ChangeError(f"{pod} is declared {len(at)} times in the Podfile")
        if at:
            lines[at[0]] = _with_version(lines[at[0]], pod, version)
        else:
            to_add.append((pod, version))
    if not to_add:
        return "".join(lines)

    sdk = declared.get(SDK_POD, [])
    if len(sdk) != 1:
        raise ChangeError(
            f"adapters are added next to {SDK_POD}, which the Podfile must declare once"
        )
    # Insert after the SDK line and any AppLovin pods directly below it
    end = sdk[0]
    while end + 1 < len(lines) and _is_applovin_pod(lines[end + 1]):
        end += 1
    sdk_line = lines[sdk[0]]
    indent = sdk_line[: len(sdk_line) - len(sdk_line.lstrip())]
    ending = "\r\n" if sdk_line.endswith("\r\n") else "\n"
    if not lines[end].endswith("\n"):
        lines[end] += ending
    lines[end + 1 : end + 1] = [
        f"{indent}pod '{pod}', '{version}'{ending}" for pod, version in to_add
    ]
    return "".join(lines)


def _is_applovin_pod(line: str) -> bool:
    match = POD_RE.match(line.split("#", 1)[0])
    return bool(match and match.group(1).startswith("AppLovin"))


def _with_version(line: str, pod: str, version: str) -> str:
    """
    `line` with its version constraints replaced by exactly `version`, keeping other options and
    any comment, unless the constraints already allow `version`.
    """
    body = line.rstrip("\r\n")
    code, sep, comment = body.partition("#")
    match = POD_RE.match(code)
    assert match is not None
    allowed = allows_version(POD_VERSION_RE.findall(match.group(2)), version)
    if allowed is None:
        raise ChangeError(f"cannot read the version constraint of {pod}: {code.strip()}")
    if allowed:
        return line
    indent = code[: len(code) - len(code.lstrip())]
    options = POD_VERSION_RE.sub("", match.group(2))
    return f"{indent}pod '{pod}', '{version}'{options}{sep}{comment}{line[len(body) :]}"


def _app_info_plist(root: Path, files: list[str]) -> str:
    """
    The one Info.plist that is not an app extension's (extensions declare `NSExtension`).
    """
    plists = [file for file in files if PurePosixPath(file).name == "Info.plist"]
    app = [file for file in plists if "NSExtension" not in _load_plist(_read(root, file), file)]
    if len(app) != 1:
        raise ChangeError(f"cannot tell which Info.plist belongs to the app: {plists}")
    return app[0]


def _load_plist(text: str, rel: str) -> dict[str, Any]:
    try:
        data = plistlib.loads(text.encode("utf-8"))
    except (plistlib.InvalidFileException, ValueError) as exc:
        raise ChangeError(f"{rel} is not a readable plist: {exc}") from exc
    if not isinstance(data, dict):
        raise ChangeError(f"{rel} is not a dictionary plist")
    return data


def _add_plist_string(text: str, rel: str, key: str, value: str) -> str:
    """
    `text` with `key` added at the end of the top-level dictionary, keeping all other bytes.
    """
    end = text.rfind("</dict>")
    if end == -1 or "</plist>" not in text[end:]:
        raise ChangeError(f"{rel} is not an XML plist")
    line_start = text.rfind("\n", 0, end) + 1
    indent_match = _PLIST_KEY_INDENT_RE.search(text)
    indent = indent_match.group(1) if indent_match else "\t"
    entry = f"{indent}<key>{escape(key)}</key>\n{indent}<string>{escape(value)}</string>\n"
    new = text[:line_start] + entry + text[line_start:]
    if _load_plist(new, rel) != {**_load_plist(text, rel), key: value}:
        raise ChangeError(f"cannot add {key} to {rel} without changing other entries")
    return new

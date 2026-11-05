"""
Read-only file access inside one repository: walking, searching and reading lines.
"""

from __future__ import annotations

import fnmatch
import os
import re
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel

from adtech_agents.tools.common import AuditContext, ToolError, tool_error

# Build output and installed third-party code (CocoaPods), skipped at any depth.
SKIP_DIRS = frozenset({"build", "Pods", "DerivedData", "Carthage", "node_modules"})

MAX_FILE_BYTES = 2_000_000
MAX_SEARCH_HITS = 50
MAX_READ_LINES = 200
MAX_LINE_CHARS = 500


class SearchHit(BaseModel):
    path: str
    line: int
    text: str


class SearchResult(BaseModel):
    hits: list[SearchHit]
    truncated: bool


class FileExcerpt(BaseModel):
    path: str
    total_lines: int
    lines: list[str]
    """
    Numbered lines, e.g. `"14: ALSdk.shared().initialize(with: initConfig) { _ in"`.
    """


# Entry points for OAI SDK tool calling. The docstrings are the tool descriptions the model sees.
@function_tool(name_override="search_code", failure_error_function=tool_error)
def search_code_tool(
    ctx: RunContextWrapper[AuditContext], query: str, glob: str | None, regex: bool
) -> str:
    """
    Search project source line by line; returns path, line number and text per hit (max 50).
    Pods/ and build output are excluded.

    Args:
        query: Text to find, or a Python regular expression when regex is true.
        glob: File filter such as "*.swift" or "App/Ads/*", or null for all files.
        regex: Treat query as a regular expression.
    """
    return search_code(query, glob, regex, ctx.context.repo_root).model_dump_json()


@function_tool(name_override="read_file_lines", failure_error_function=tool_error)
def read_file_lines_tool(
    ctx: RunContextWrapper[AuditContext], path: str, start_line: int, end_line: int
) -> str:
    """
    Read numbered lines of a repository file (1-based, inclusive, at most 200 lines).

    Args:
        path: Repository-relative path, e.g. "PuzzleQuest/AppDelegate.swift".
        start_line: First line to return.
        end_line: Last line to return.
    """
    excerpt = read_file_lines(path, start_line, end_line, ctx.context.repo_root)
    return excerpt.model_dump_json()


def iter_files(root: Path) -> Iterator[str]:
    """
    Yield repo-relative POSIX paths of regular, non-hidden files in sorted order.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        rel_dir = "" if current == root else current.relative_to(root).as_posix()
        dirnames[:] = sorted(
            name
            for name in dirnames
            if not name.startswith(".")
            and name not in SKIP_DIRS
            and not (current / name).is_symlink()
        )
        for name in sorted(filenames):
            if not name.startswith(".") and not (current / name).is_symlink():
                yield f"{rel_dir}/{name}".lstrip("/")


def read_text(path: Path) -> str | None:
    """
    File contents, or `None` for large or binary files.
    """
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    return data.decode("utf-8", errors="replace")


def resolve_repo_file(relative_path: str, root: Path) -> Path:
    """
    Resolve a model-supplied path, refusing anything outside `root` or hidden.
    """
    parts = PurePosixPath(relative_path.replace("\\", "/")).parts
    if not parts or parts[0] == "/" or ".." in parts:
        raise ToolError("path must be relative to the repository root, without '..'")
    if any(part.startswith(".") for part in parts):
        raise ToolError("hidden files are not readable")
    resolved = root.joinpath(*parts).resolve()
    if not resolved.is_relative_to(root):
        raise ToolError("path resolves outside the repository")
    if not resolved.is_file():
        raise ToolError(f"not a file: {relative_path}")
    return resolved


def _glob_matches(rel: str, glob: str) -> bool:
    target = rel if "/" in glob else PurePosixPath(rel).name
    return fnmatch.fnmatchcase(target, glob)


def search_code(query: str, glob: str | None, regex: bool, root: Path) -> SearchResult:
    """
    Line search over project source; `Pods/` and build output are excluded.
    """
    if not query.strip():
        raise ToolError("query must not be empty")
    try:
        pattern = re.compile(query if regex else re.escape(query))
    except re.error as exc:
        raise ToolError(f"invalid regular expression: {exc}") from exc
    hits: list[SearchHit] = []
    for rel in iter_files(root):
        if glob and not _glob_matches(rel, glob):
            continue
        text = read_text(root / rel)
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                if len(hits) == MAX_SEARCH_HITS:
                    return SearchResult(hits=hits, truncated=True)
                _check_line_length(line, rel, number)
                hits.append(SearchHit(path=rel, line=number, text=line.strip()))
    return SearchResult(hits=hits, truncated=False)


def read_repo_lines(relative_path: str, root: Path) -> tuple[str, list[str]]:
    """
    Normalized repo-relative path and all lines of a readable text file.
    """
    path = resolve_repo_file(relative_path, root)
    text = read_text(path)
    if text is None:
        raise ToolError(f"{relative_path} is binary or too large")
    return path.relative_to(root).as_posix(), text.splitlines()


def read_file_lines(relative_path: str, start_line: int, end_line: int, root: Path) -> FileExcerpt:
    """
    Lines `start_line..end_line` (1-based, inclusive), capped at `MAX_READ_LINES`.
    """
    rel, lines = read_repo_lines(relative_path, root)
    if start_line < 1 or end_line < start_line:
        raise ToolError("line range must satisfy 1 <= start_line <= end_line")
    end = min(end_line, start_line + MAX_READ_LINES - 1, len(lines))
    numbered = []
    for n in range(start_line, end + 1):
        _check_line_length(lines[n - 1], rel, n)
        numbered.append(f"{n}: {lines[n - 1]}")
    return FileExcerpt(path=rel, total_lines=len(lines), lines=numbered)


def _check_line_length(line: str, rel: str, number: int) -> None:
    """
    Refuse lines over `MAX_LINE_CHARS` (minified or generated files) rather than cut them.
    """
    if len(line) > MAX_LINE_CHARS:
        raise ToolError(
            f"{rel}:{number} is {len(line)} chars (limit {MAX_LINE_CHARS}); "
            "likely generated, narrow the search with glob or skip this file"
        )

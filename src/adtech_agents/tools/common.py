"""
Shared by every agent tool: the run context they are bound to and how their errors reach the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import RunContextWrapper

from adtech_agents.schemas import RepositoryInfo


@dataclass
class AuditContext:
    """
    Per-audit state handed to every tool.
    """

    repo_root: Path
    repository_info: RepositoryInfo


class ToolError(ValueError):
    """
    Invalid tool input. The message is returned to the model.
    """


def tool_error(ctx: RunContextWrapper[Any], error: Exception) -> str:
    """
    Show the model why its input was refused, but not internals of unexpected failures.
    """
    if isinstance(error, ToolError):
        return f"error: {error}"
    return f"error: internal tool failure ({type(error).__name__})"

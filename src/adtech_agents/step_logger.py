"""
`StepLogger`: one log line per model turn and tool call, plus a summary when the run ends. As each
tool call starts it also logs a readable line ("Searching the code for …") on `PROGRESS_LOGGER`,
which the quiet chat keeps showing.

Full prompts and responses stay out of the console; see `Config.LOG_AGENT_DATA` for those.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from agents import Agent, RunContextWrapper, RunHooks, Tool
from agents.items import ModelResponse, TResponseInputItem
from agents.run_context import AgentHookContext
from agents.tool_context import ToolContext

from adtech_agents.tools.common import AuditContext

MAX_ARGS_CHARS = 120
MAX_QUERY_CHARS = 60
PROGRESS_LOGGER = "adtech.progress"


class StepLogger(RunHooks[AuditContext]):
    turn: int
    started: float

    def __init__(self) -> None:
        self.turn = 0
        self.started = time.monotonic()

    async def on_agent_start(
        self, context: AgentHookContext[AuditContext], agent: Agent[Any]
    ) -> None:
        self.started = time.monotonic()
        logging.info(f"{agent.name}: started on {context.context.repo_root.name}")

    async def on_llm_start(
        self,
        context: RunContextWrapper[AuditContext],
        agent: Agent[AuditContext],
        system_prompt: str | None,
        input_items: list[TResponseInputItem],
    ) -> None:
        self.turn += 1

    async def on_llm_end(
        self,
        context: RunContextWrapper[AuditContext],
        agent: Agent[AuditContext],
        response: ModelResponse,
    ) -> None:
        usage = response.usage
        logging.info(
            f"turn {self.turn}  model  {usage.input_tokens} in / {usage.output_tokens} out tokens"
        )

    async def on_tool_start(
        self, context: RunContextWrapper[AuditContext], agent: Agent[Any], tool: Tool
    ) -> None:
        args = context.tool_arguments if isinstance(context, ToolContext) else ""
        logging.getLogger(PROGRESS_LOGGER).info(describe_tool_call(tool.name, args))

    async def on_tool_end(
        self,
        context: RunContextWrapper[AuditContext],
        agent: Agent[Any],
        tool: Tool,
        result: object,
    ) -> None:
        args = context.tool_arguments if isinstance(context, ToolContext) else ""
        if len(args) > MAX_ARGS_CHARS:
            args = args[:MAX_ARGS_CHARS] + "…"
        logging.info(f"turn {self.turn}  {tool.name}({args}) -> {_summarize(result)}")

    async def on_agent_end(
        self, context: AgentHookContext[AuditContext], agent: Agent[Any], output: Any
    ) -> None:
        findings = getattr(output, "findings", None)
        outcome = f"{len(findings)} findings" if findings is not None else "done"
        usage = context.usage
        logging.info(
            f"{agent.name}: {outcome} in {time.monotonic() - self.started:.1f}s "
            f"({usage.requests} model calls, {usage.total_tokens} tokens)"
        )


def describe_tool_call(name: str, arguments: str) -> str:
    """
    A line for the publisher, e.g. `Reading PuzzleQuest/AppDelegate.swift, lines 1-40…`.
    """
    try:
        args = json.loads(arguments) if arguments else {}
    except ValueError:
        args = {}
    if not isinstance(args, dict):
        args = {}
    match name:
        case "inspect_app_project":
            return "Reading the Podfile and Info.plist…"
        case "search_code":
            query = _shown(args.get("query"), MAX_QUERY_CHARS)
            where = _shown(args["glob"], MAX_QUERY_CHARS) if args.get("glob") else "the code"
            return f'Searching {where} for "{query}"…'
        case "read_file_lines":
            path = _shown(args.get("path"), MAX_ARGS_CHARS)
            return f"Reading {path}, lines {args.get('start_line')}-{args.get('end_line')}…"
        case _:
            return f"Running {name}…"


def _shown(value: object, limit: int) -> str:
    """
    A model-chosen argument made safe to print: the model reads untrusted repository content, so
    control characters (terminal escapes, newlines) are replaced and long values cut.
    """
    text = "".join(c if c.isprintable() else "?" for c in str(value))
    return text if len(text) <= limit else text[:limit] + "…"


def _summarize(result: object) -> str:
    """
    Short description of a tool result, e.g. `3 hits` or `20 lines`.
    """
    text = str(result)
    if text.startswith("error:"):
        return text
    try:
        data = json.loads(text)
    except ValueError:
        return f"{len(text)} chars"
    if not isinstance(data, dict):
        return f"{len(text)} chars"
    if "hits" in data:
        return f"{len(data['hits'])} hits" + (" (truncated)" if data.get("truncated") else "")
    if "lines" in data:
        return f"{len(data['lines'])} of {data.get('total_lines')} lines"
    if "dependencies" in data:
        return f"{len(data['dependencies'])} AppLovin pods"
    return f"{len(text)} chars"

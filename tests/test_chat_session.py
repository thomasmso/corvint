from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from agents import Agent, Model, ModelResponse, TResponseInputItem, Usage
from agents.items import TResponseOutputItem, TResponseStreamEvent
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

from adtech_agents import chat_session
from adtech_agents.chat_session import GREETING, ChatSession
from adtech_agents.config import Config
from adtech_agents.context import Context
from adtech_agents.tools import chat_tools
from adtech_agents.tools.chat_tools import AuditResult, ChatState
from adtech_agents.workflows.install_pods_workflow import InstallResult


class ScriptedModel(Model):
    """
    Returns the scripted outputs in order and records the input of every call.
    """

    def __init__(self, outputs: list[TResponseOutputItem]) -> None:
        self.outputs = outputs
        self.inputs: list[list[TResponseInputItem]] = []

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        model_input = kwargs.get("input", args[1] if len(args) > 1 else None)
        assert isinstance(model_input, list)
        self.inputs.append(model_input)
        return ModelResponse(output=[self.outputs.pop(0)], usage=Usage(), response_id=None)

    def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[TResponseStreamEvent]:
        raise NotImplementedError


def _call(name: str, **arguments: Any) -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall(
        type="function_call", call_id=f"call-{name}", name=name, arguments=json.dumps(arguments)
    )


def _reply(text: str) -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id="msg",
        type="message",
        role="assistant",
        status="completed",
        content=[ResponseOutputText(type="output_text", text=text, annotations=[])],
    )


def test_conversation_keeps_history_across_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    model = ScriptedModel(
        [
            _call("audit_project", source="https://github.com/acme/puzzle"),
            _reply("The Google adapter is missing. Open a pull request?"),
            _call("install_pods", pods=["AppLovinMediationGoogleAdapter"]),
            _reply("Opened https://github.com/acme/puzzle/pull/1"),
        ]
    )
    build = chat_session.build_max_chat_agent

    def build_with_model(allow_local_paths: bool) -> Agent[ChatState]:
        return build(allow_local_paths).clone(model=model)

    async def fake_audit(state: ChatState, source: str) -> AuditResult:
        state.source = source
        return AuditResult(source=source, note="n", summary="Google adapter missing.", findings=[])

    async def fake_install(state: ChatState, pods: list[str]) -> InstallResult:
        assert state.source == "https://github.com/acme/puzzle"
        return InstallResult(pull_request_url=f"{state.source}/pull/1", diff="d")

    monkeypatch.setattr(chat_session, "build_max_chat_agent", build_with_model)
    monkeypatch.setattr(chat_tools, "audit_project", fake_audit)
    monkeypatch.setattr(chat_tools, "install", fake_install)

    ctx = Context.create(Config())
    session = ChatSession(ctx, allow_local_paths=False)

    async def converse() -> list[str]:
        return [
            await session.send("Audit https://github.com/acme/puzzle"),
            await session.send("Yes please"),
        ]

    replies = asyncio.run(converse())
    ctx.shutdown()

    assert replies == [
        "The Google adapter is missing. Open a pull request?",
        "Opened https://github.com/acme/puzzle/pull/1",
    ]
    history = json.dumps(model.inputs[2])
    for earlier in (GREETING, "Audit https://github.com/acme/puzzle", "Google adapter missing."):
        assert json.dumps(earlier)[1:-1] in history
    assert "pull/1" in json.dumps(model.inputs[3])

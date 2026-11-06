"""
MAX Chat Agent: talks with a publisher, audits their iOS project and opens a pull request with the
pods it needs. The audit itself is the read-only iOS MAX Audit Agent, run by `audit_project`.

What the agent says and the order it works in come from `prompts/<locale>/chat.toml`; what it may
do is enforced by its tools.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from importlib import resources

from agents import Agent

from adtech_agents.reference_data import ADAPTER_PODS
from adtech_agents.tools.chat_tools import ChatState, audit_project_tool, install_pods_tool
from adtech_agents.tools.inspect_app_project import SDK_POD


@dataclass(frozen=True)
class ChatText:
    """
    The contents of one locale's `chat.toml`.
    """

    greeting: str
    terminal_quit_hint: str
    source_hint_local: str
    source_hint_github: str
    instructions: str
    """
    Template; see `build_max_chat_agent` for the placeholders.
    """


def load_chat_text(locale: str) -> ChatText:
    path = resources.files("adtech_agents").joinpath("prompts", locale, "chat.toml")
    if not path.is_file():
        raise ValueError(f"no chat text for locale {locale!r}")
    return ChatText(**tomllib.loads(path.read_text(encoding="utf-8")))


def build_max_chat_agent(text: ChatText, allow_local_paths: bool) -> Agent[ChatState]:
    pods = [f"- {pod}" for pod in (SDK_POD, *ADAPTER_PODS.values())]
    return Agent[ChatState](
        name="MAX Chat Agent",
        instructions=text.instructions.format(
            source_hint=text.source_hint_local if allow_local_paths else text.source_hint_github,
            sdk_pod=SDK_POD,
            admob_pod=ADAPTER_PODS["ADMOB_NETWORK"],
            unity_pod=ADAPTER_PODS["UNITY_NETWORK"],
            pods="\n".join(pods),
        ),
        tools=[audit_project_tool, install_pods_tool],
    )

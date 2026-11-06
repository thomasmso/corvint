"""
`ChatSession`: one conversation with a publisher, shared by every interface (terminal now, Slack
later). The interface shows `text.greeting`, passes in each message and shows the reply.
"""

from __future__ import annotations

import asyncio

from agents import RunConfig, Runner, TResponseInputItem

from adtech_agents.agents.max_chat_agent import build_max_chat_agent, load_chat_text
from adtech_agents.context import Context
from adtech_agents.tools.chat_tools import ChatState


class ChatSession:
    def __init__(self, ctx: Context, allow_local_paths: bool) -> None:
        self._ctx = ctx
        self.text = load_chat_text(ctx.config.CHAT_LOCALE)
        self._state = ChatState(ctx=ctx, allow_local_paths=allow_local_paths)
        self._agent = build_max_chat_agent(self.text, allow_local_paths)
        self._history: list[TResponseInputItem] = [
            {"role": "assistant", "content": self.text.greeting}
        ]
        # Replies run one at a time, so a second message waits for the first reply
        self._lock = asyncio.Lock()

    async def send(self, message: str) -> str:
        """
        The agent's reply to `message`, after any audit or pull request it runs.
        """
        async with self._lock:
            result = await Runner.run(
                self._agent,
                [*self._history, {"role": "user", "content": message}],
                context=self._state,
                max_turns=self._ctx.config.MAX_TURNS,
                run_config=RunConfig(tracing_disabled=True),
            )
            self._history = result.to_input_list()
            return str(result.final_output)

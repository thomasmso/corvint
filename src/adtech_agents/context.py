"""
Application context holding the configuration and shared resources.
"""

from dataclasses import dataclass

from adtech_agents.config import Config
from commons.task_manager import TaskManager


@dataclass
class Context:
    """
    Created once by the CLI and passed down to workflows (later: orchestrator and subagents).

    Usage:
        ctx = Context.create(Config())
        results = ctx.task_manager.submit_tasks([...], ExecutorType.THREAD)
        ctx.shutdown()  # optional, auto-called on exit
    """

    config: Config
    task_manager: TaskManager

    @classmethod
    def create(cls, config: Config) -> "Context":
        return cls(
            config=config,
            task_manager=TaskManager(thread_pool_size=config.THREAD_POOL_SIZE),
        )

    def shutdown(self) -> None:
        """
        Shut down resources. Safe to call multiple times.
        """
        self.task_manager.shutdown()

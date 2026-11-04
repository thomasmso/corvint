"""
Application context holding shared resources.
"""

from dataclasses import dataclass

from commons.task_manager import TaskManager


@dataclass
class Context[C]:
    """
    Application context holding shared resources.

    Usage:
        ctx = Context.create(cfg)
        results = ctx.task_manager.submit_tasks([...])
        ctx.shutdown()  # optional, auto-called on exit
    """

    cfg: C
    task_manager: TaskManager

    @classmethod
    def create(cls, cfg: C, thread_pool_size: int = 8) -> "Context[C]":
        """Create a Context with initialized TaskManager."""
        return cls(
            cfg=cfg,
            task_manager=TaskManager(thread_pool_size=thread_pool_size),
        )

    def shutdown(self) -> None:
        """Shut down resources. Safe to call multiple times."""
        self.task_manager.shutdown()

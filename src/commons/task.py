"""
Task abstraction for parallelizable work units.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any


class ExecutorType(Enum):
    """Type of executor to use for task execution."""

    PROCESS = "process"  # ProcessPoolExecutor - uses separate CPU cores
    THREAD = "thread"  # ThreadPoolExecutor - lighter weight, shared memory


class Task(ABC):
    """
    Base class for parallelizable work units.

    Subclass and override `run()` with your work, or use `FunctionTask` for simple cases.
    """

    @abstractmethod
    def run(self) -> Any:
        """Execute the task. Override in subclasses."""
        pass


class FunctionTask[T](Task):
    """
    Task that wraps a module-level callable.

    Note: The function must be defined at module level (not a lambda or closure)
    because ProcessPoolExecutor requires picklable objects.
    """

    fn: Callable[..., T]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    def __init__(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> None:
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self) -> T:
        return self.fn(*self.args, **self.kwargs)

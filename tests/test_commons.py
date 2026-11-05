from __future__ import annotations

import pytest

from commons import ExecutorType, FunctionTask, TaskManager, string_utils


def _square(value: int) -> int:
    return value * value


@pytest.mark.parametrize("executor_type", [ExecutorType.THREAD, ExecutorType.PROCESS])
def test_task_manager_returns_results_in_order(executor_type: ExecutorType) -> None:
    task_manager = TaskManager(thread_pool_size=2)
    try:
        tasks = [FunctionTask(_square, n) for n in range(5)]
        assert task_manager.submit_tasks(tasks, executor_type) == [0, 1, 4, 9, 16]
    finally:
        task_manager.shutdown()


def test_string_utils() -> None:
    assert string_utils.default_if_empty("  ", "x") == "x"
    assert string_utils.contains_ignoring_case("OnAdReceivedRewardEvent", "reward")

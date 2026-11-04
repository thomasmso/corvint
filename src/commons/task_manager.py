from __future__ import annotations

import atexit
import logging
import os
import sys
import threading
import time
from collections.abc import Iterable
from concurrent.futures import (
    Executor,
    Future,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
)
from queue import Queue
from typing import Any

from tqdm import tqdm

from commons.task import ExecutorType, Task


class TaskManager:
    """
    Centralized manager for parallel task execution.

    - ProcessPoolExecutor: CPU-bound tasks (bypasses GIL, uses cpu_count workers)
    - ThreadPoolExecutor: I/O-bound tasks (configurable pool size for network calls)

    Usage:
        task_manager = TaskManager(thread_pool_size=16)
        results = task_manager.submit_tasks(tasks, ExecutorType.THREAD)
    """

    def __init__(self, thread_pool_size: int = 8) -> None:
        self._thread_pool_size = thread_pool_size
        self._process_executor: ProcessPoolExecutor | None = ProcessPoolExecutor(
            max_workers=os.cpu_count(),
            initializer=_init_worker,
        )
        self._thread_executor: ThreadPoolExecutor | None = ThreadPoolExecutor(
            max_workers=thread_pool_size,
        )
        atexit.register(self.shutdown)

    def submit_task(self, task: Task, executor_type: ExecutorType) -> Future[Any]:
        """
        Submit a single task for execution. Returns a Future.

        Args:
            task: The task to execute
            executor_type: Type of executor to use
        """
        executor = self._get_executor(executor_type)
        return executor.submit(_run_task, task)

    def submit_tasks(
        self, tasks: Iterable[Task], executor_type: ExecutorType, desc: str | None = None
    ) -> list[Any]:
        """
        Execute multiple tasks in parallel and return results in order.

        Args:
            tasks: Iterable of tasks to execute
            executor_type: Type of executor to use for all tasks
            desc: Optional description for progress bar

        Returns:
            List of results in the same order as the input tasks
        """
        task_list = list[Task](tasks)
        if not task_list:
            return []

        executor = self._get_executor(executor_type)

        if desc:
            results = [None] * len(task_list)
            futures = {executor.submit(_run_task, task): i for i, task in enumerate(task_list)}

            with tqdm(total=len(task_list), desc=desc) as pbar:
                for future in as_completed(futures):
                    index = futures[future]
                    results[index] = future.result()
                    pbar.update(1)

            return results

        return list[Any](executor.map(_run_task, task_list))

    def map_networking_tasks(
        self,
        tasks: Iterable[Task],
        desc: str,
        delay_seconds: float = 0.0,
    ) -> list[Any]:
        """
        Execute multiple I/O tasks in parallel using the thread pool.

        Args:
            tasks: Iterable of I/O tasks to execute
            desc: Description for progress bar
            delay_seconds: If > 0, each worker sleeps this long after finishing
                a task before taking another one. This fills the thread pool
                immediately, then spaces out follow-up request starts against
                rate-limited APIs.

        Returns:
            List of results in the same order as the input tasks
        """
        task_list = list[Task](tasks)
        if not task_list:
            return []

        if self._thread_executor is None:
            raise RuntimeError("Thread executor has been shut down")

        if delay_seconds <= 0:
            results = [None] * len(task_list)
            futures = [self._thread_executor.submit(_run_task, task) for task in task_list]
            with tqdm(total=len(task_list), desc=desc) as pbar:
                future_to_index = {f: i for i, f in enumerate(futures)}
                for future in as_completed(futures):
                    results[future_to_index[future]] = future.result()
                    pbar.update(1)
            return results
        # Throttled path: fill the thread pool immediately. When a worker
        # finishes one task, it waits before claiming another task.
        results = [None] * len(task_list)
        done_queue: Queue[tuple[int, Any, BaseException | None]] = Queue()
        next_task_index = 0
        next_task_lock = threading.Lock()

        def _run_worker() -> None:
            nonlocal next_task_index

            while True:
                with next_task_lock:
                    if next_task_index >= len(task_list):
                        return
                    index = next_task_index
                    next_task_index += 1

                try:
                    result = _run_task(task_list[index])
                    done_queue.put((index, result, None))
                except BaseException as e:
                    done_queue.put((index, None, e))
                    return

                with next_task_lock:
                    has_more_work = next_task_index < len(task_list)
                if has_more_work:
                    time.sleep(delay_seconds)

        worker_count = min(self._thread_pool_size, len(task_list))
        worker_futures = [self._thread_executor.submit(_run_worker) for _ in range(worker_count)]

        with tqdm(total=len(task_list), desc=desc) as pbar:
            for _ in range(len(task_list)):
                index, result, error = done_queue.get()
                if error is not None:
                    for future in worker_futures:
                        future.cancel()
                    raise error

                results[index] = result
                pbar.update(1)

        for future in worker_futures:
            future.result()

        return results

    def shutdown(self) -> None:
        """
        Shut down all executors. Safe to call multiple times.
        """
        if self._process_executor:
            self._process_executor.shutdown(wait=True)
            self._process_executor = None
        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
            self._thread_executor = None

    def _get_executor(self, executor_type: ExecutorType) -> Executor:
        """
        Get the appropriate executor for the given executor type.
        """
        if executor_type == ExecutorType.PROCESS:
            if self._process_executor is None:
                raise RuntimeError("Process executor has been shut down")
            return self._process_executor
        else:  # ExecutorType.THREAD
            if self._thread_executor is None:
                raise RuntimeError("Thread executor has been shut down")
            return self._thread_executor


def _init_worker() -> None:
    """
    Initialize logging for worker processes. Called once per worker at startup.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        # stdout so Cloud Logging doesn't mark INFO lines as ERROR (stderr default)
        stream=sys.stdout,
    )


def _run_task(task: Task) -> Any:
    """
    Wrapper to call task.run() - needed for pickling by ProcessPoolExecutor.
    """
    return task.run()

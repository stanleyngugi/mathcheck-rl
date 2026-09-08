"""Small event-loop-local exact-input single-flight cache for verifier results."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class AsyncSingleFlight(Generic[T]):
    def __init__(self, max_completed: int = 1024):
        if max_completed < 1:
            raise ValueError("max_completed must be positive")
        self._max_completed = max_completed
        self._completed: OrderedDict[str, T] = OrderedDict()
        self._inflight: dict[str, asyncio.Task[T]] = {}
        self._lock: asyncio.Lock | None = None

    def _event_loop_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        lock = self._event_loop_lock()
        async with lock:
            if key in self._completed:
                value = self._completed.pop(key)
                self._completed[key] = value
                return value
            task = self._inflight.get(key)
            if task is None:
                task = asyncio.create_task(factory())
                self._inflight[key] = task
        try:
            value = await asyncio.shield(task)
        except BaseException:
            async with lock:
                if self._inflight.get(key) is task and task.done():
                    self._inflight.pop(key, None)
            raise
        async with lock:
            if self._inflight.get(key) is task:
                self._inflight.pop(key, None)
                self._completed[key] = value
                while len(self._completed) > self._max_completed:
                    self._completed.popitem(last=False)
        return value

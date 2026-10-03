"""Event-loop-local single-flight work with bounded completed-result reuse."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from weakref import WeakKeyDictionary

T = TypeVar("T")


@dataclass
class _LoopState(Generic[T]):
    completed: OrderedDict[str, T] = field(default_factory=OrderedDict)
    inflight: dict[str, asyncio.Task[T]] = field(default_factory=dict)


class AsyncSingleFlight(Generic[T]):
    def __init__(self, max_completed: int = 1024):
        if max_completed < 1:
            raise ValueError("max_completed must be positive")
        self._max_completed = max_completed
        self._loops: WeakKeyDictionary[asyncio.AbstractEventLoop, _LoopState[T]] = WeakKeyDictionary()

    async def get(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
        *,
        cache_result: Callable[[T], bool] | None = None,
    ) -> T:
        loop = asyncio.get_running_loop()
        state = self._loops.setdefault(loop, _LoopState())
        # These lookups and task publication contain no await. All access to
        # this state, including done callbacks, happens on its owning loop.
        if key in state.completed:
            value = state.completed.pop(key)
            state.completed[key] = value
            return value
        task = state.inflight.get(key)
        if task is None:
            task = asyncio.create_task(factory())
            state.inflight[key] = task

            def finish(done: asyncio.Task[T]) -> None:
                if state.inflight.get(key) is not done:
                    return
                state.inflight.pop(key)
                if done.cancelled():
                    return
                try:
                    value = done.result()
                except BaseException:
                    # Observe exceptions even when every consumer cancelled.
                    return
                if cache_result is not None and not cache_result(value):
                    return
                state.completed[key] = value
                while len(state.completed) > self._max_completed:
                    state.completed.popitem(last=False)

            task.add_done_callback(finish)
        # Completion owns cleanup, so cancelling any/all consumers cannot
        # remove running work or leave completed work in the in-flight map.
        return await asyncio.shield(task)

import asyncio

from native_verify.async_cache import AsyncSingleFlight


def test_concurrent_requests_are_single_flight_and_exact_input_bound():
    async def scenario():
        cache = AsyncSingleFlight(max_completed=2)
        calls = []

        async def factory(value):
            calls.append(value)
            await asyncio.sleep(0)
            return value

        first, second = await asyncio.gather(
            cache.get("same", lambda: factory(1)),
            cache.get("same", lambda: factory(1)),
        )
        third = await cache.get("different", lambda: factory(2))
        assert (first, second, third) == (1, 1, 2)
        assert calls == [1, 2]

    asyncio.run(scenario())

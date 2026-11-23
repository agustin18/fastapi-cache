"""Independent adversarial regressions for #85's indexed heap and lock.

These tests exercise invariants beyond the seed/state machine in the original
feature branch. No external cache, clock sleeps, or additional dependencies.
"""

import asyncio
import random
from typing import Dict, Optional

import pytest

from fastapi_cache.backends.inmemory import InMemoryBackend, _ExpirationIndex


@pytest.mark.parametrize("seed", range(12))
def test_indexed_heap_exactness_under_direct_arbitrary_mutations(seed: int) -> None:
    """Compare all heap positions and expiry minima against a simple oracle."""
    rng = random.Random(seed)  # noqa: S311 - deterministic invariant testing
    index = _ExpirationIndex()
    expected: Dict[str, int] = {}
    names = [f"key:{i}" for i in range(47)]

    for _ in range(1800):
        name = rng.choice(names)
        action = rng.randrange(100)
        if action < 55:
            expiry: Optional[int] = rng.choice(
                [None, -10, -1, 0, 0, 0, 1, 1, 3, 10, 100]
            )
            index.update(name, expiry)
            expected.pop(name, None)
            if expiry is not None:
                expected[name] = expiry
        elif action < 80:
            index.discard(name)
            expected.pop(name, None)
        else:
            now = rng.choice([-10, -1, 0, 1, 2, 10, 100, 101])
            earliest = min(
                ((expiry, key) for key, expiry in expected.items()),
                default=None,
            )
            actual = index.oldest_expired(now)
            wanted = (
                earliest[1]
                if earliest is not None and earliest[0] <= now
                else None
            )
            assert actual == wanted

        heap = index._heap  # pyright: ignore[reportPrivateUsage]
        positions = index._positions  # pyright: ignore[reportPrivateUsage]
        assert len(index) == len(expected)
        assert len(heap) == len(positions) == len(expected)
        assert {key: expiry for expiry, key in heap} == expected
        assert set(positions) == set(expected)
        for position, (expiry, key) in enumerate(heap):
            assert positions[key] == position
            if position:
                assert heap[(position - 1) // 2] <= (expiry, key)


def test_get_with_ttl_updates_lru_order_without_changing_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_with_ttl is a successful access and must protect the read key."""
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: 1000)

    async def run() -> None:
        backend = InMemoryBackend(max_entries=2)
        await backend.set("cache:a", b"a", expire=9)
        await backend.set("cache:b", b"b", expire=9)
        assert await backend.get_with_ttl("cache:a") == (9, b"a")
        await backend.set("cache:c", b"c", expire=9)
        assert await backend.get("cache:a") == b"a"
        assert await backend.get("cache:b") is None
        assert await backend.get("cache:c") == b"c"
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 2  # pyright: ignore[reportPrivateUsage]

    asyncio.run(run())


def test_cancelled_waiter_cannot_modify_heap_or_store() -> None:
    """A task cancelled while awaiting the lock does not partly write."""
    async def run() -> None:
        backend = InMemoryBackend(max_entries=1)
        await backend.set("n:keep", b"keep", expire=30)
        async with backend._get_lock():  # pyright: ignore[reportPrivateUsage]
            waiting = asyncio.create_task(backend.set("n:cancel", b"x", expire=1))
            await asyncio.sleep(0)
            waiting.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiting

        assert await backend.get("n:keep") == b"keep"
        assert await backend.get("n:cancel") is None
        assert len(backend._store) == 1  # pyright: ignore[reportPrivateUsage]
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 1  # pyright: ignore[reportPrivateUsage]
        assert backend._recency is not None  # pyright: ignore[reportPrivateUsage]
        assert list(backend._recency) == ["n:keep"]  # pyright: ignore[reportPrivateUsage]

    asyncio.run(run())


def test_zero_ttl_is_not_replayed_at_exact_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """At the deadline a zero-TTL value must not be returned as a cache hit."""
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend(max_entries=1)
        await backend.set("n:edge", b"edge", expire=0)
        assert await backend.get("n:edge") is None
        assert await backend.get_with_ttl("n:edge") == (0, None)
        assert len(backend._store) == 0  # pyright: ignore[reportPrivateUsage]
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 0  # pyright: ignore[reportPrivateUsage]

    asyncio.run(run())

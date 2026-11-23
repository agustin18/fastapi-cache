"""Precise InMemory TTL deadline semantics proposed for the 0.7 contract.

No real sleeps or system clock dependencies; tests exercise unbounded and
bounded storage including the heap's full-capacity reclamation decision.
"""

import asyncio
from typing import Optional

import pytest

from fastapi_cache.backends.inmemory import InMemoryBackend


@pytest.mark.parametrize("capacity", [None, 2])
def test_exact_deadline_is_not_a_cache_hit(
    capacity: Optional[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    now = [5000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend(max_entries=capacity)
        await backend.set("tenant:edge", b"payload", expire=3)
        assert await backend.get_with_ttl("tenant:edge") == (3, b"payload")
        now[0] = 5002
        assert await backend.get("tenant:edge") == b"payload"
        assert await backend.get_with_ttl("tenant:edge") == (1, b"payload")
        now[0] = 5003
        assert await backend.get_with_ttl("tenant:edge") == (0, None)
        assert await backend.get("tenant:edge") is None
        now[0] = 5001  # removed entries stay removed even if clock moves backward
        assert await backend.get("tenant:edge") is None

    asyncio.run(run())


@pytest.mark.parametrize("capacity", [None, 2])
@pytest.mark.parametrize("expire", [0, -1])
def test_nonpositive_inmemory_expiry_has_no_visible_bytes(
    capacity: Optional[int], expire: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: 7000)

    async def run() -> None:
        backend = InMemoryBackend(max_entries=capacity)
        await backend.set("tenant:instant", b"confidential", expire=expire)
        assert await backend.get("tenant:instant") is None
        assert await backend.get_with_ttl("tenant:instant") == (0, None)

    asyncio.run(run())


def test_bounded_heap_reclaims_exact_deadline_before_live_lru(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [9000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend(max_entries=2)
        await backend.set("a:older-live", b"safe", expire=30)
        await backend.set("a:newer-expired", b"expired", expire=5)
        now[0] = 9005
        await backend.set("a:new", b"new", expire=30)
        assert await backend.get("a:older-live") == b"safe"
        assert await backend.get("a:newer-expired") is None
        assert await backend.get("a:new") == b"new"
        assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 2  # pyright: ignore[reportPrivateUsage]

    asyncio.run(run())

@pytest.mark.parametrize("capacity", [None, 2])
def test_backward_wall_clock_shift_on_still_live_entry(
    capacity: Optional[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Characterize wall-clock skew: an unexpired entry can gain remaining TTL.

    This documents a limitation of integer wall-clock timestamps, not a
    monotonic-clock guarantee or a promise to expire after elapsed seconds.
    """
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend(max_entries=capacity)
        await backend.set("tenant:skew", b"safe", expire=10)
        now[0] = 1003
        assert await backend.get_with_ttl("tenant:skew") == (7, b"safe")
        now[0] = 998
        assert await backend.get("tenant:skew") == b"safe"
        assert await backend.get_with_ttl("tenant:skew") == (12, b"safe")
        now[0] = 1010
        assert await backend.get_with_ttl("tenant:skew") == (0, None)
        now[0] = 999
        assert await backend.get("tenant:skew") is None

    asyncio.run(run())

"""Opt-in bounded InMemory regression contract (#54).

No change is allowed to the unbounded default, cache key format or
per-instance scoping. All tests run against the public Backend protocol.
"""

import asyncio
from typing import Dict, Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


@pytest.mark.parametrize("invalid", [0, -1, True, False, 1.5, "3", object()])
def test_invalid_max_entries_fails_closed(invalid: object) -> None:
    with pytest.raises(ValueError, match="max_entries must be"):
        InMemoryBackend(max_entries=invalid)  # type: ignore[arg-type]


@pytest.mark.parametrize("initial", [None, 2])
@pytest.mark.parametrize("attempt", [None, 0, 1, 2, 5, -1, True, "3"])
def test_max_entries_is_read_only_after_initialization(
    initial: object, attempt: object
) -> None:
    """Neither shrinking, disabling nor replacing the validated cap is legal."""
    backend = InMemoryBackend(max_entries=initial)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        setattr(backend, "max_entries", attempt)
    assert backend.max_entries == initial


def test_mutation_attempt_cannot_violate_bounded_lru_capacity() -> None:
    """The auditor's shrink-to-one reproduction must now fail closed."""
    async def run() -> None:
        backend = InMemoryBackend(max_entries=2)
        await backend.set("a", b"a")
        await backend.set("b", b"b")
        with pytest.raises(AttributeError):
            backend.max_entries = 1  # type: ignore[misc]
        with pytest.raises(AttributeError):
            backend.max_entries = None  # type: ignore[misc]
        with pytest.raises(AttributeError):
            backend.max_entries = -1  # type: ignore[misc]
        await backend.set("c", b"c")
        assert backend.max_entries == 2
        assert list(backend._store) == ["b", "c"]  # pyright: ignore[reportPrivateUsage]
        assert await backend.get("a") is None
        assert await backend.get("b") == b"b"
        assert await backend.get("c") == b"c"
        assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]
        assert backend._recency is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._recency) == 2  # pyright: ignore[reportPrivateUsage]
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 0  # pyright: ignore[reportPrivateUsage]

    asyncio.run(run())


def test_default_remains_unbounded_and_backward_compatible() -> None:
    async def run() -> None:
        backend = InMemoryBackend()
        assert backend.max_entries is None
        for i in range(101):
            await backend.set("demo:" + str(i), str(i).encode(), expire=None)
        for i in range(101):
            assert await backend.get("demo:" + str(i)) == str(i).encode()
        assert len(backend._store) == 101  # pyright: ignore[reportPrivateUsage]
        assert backend._recency is None  # pyright: ignore[reportPrivateUsage]
        assert await backend.get_with_ttl("demo:1") == (-1, b"1")
    asyncio.run(run())


def test_capacity_evicts_least_recently_read_or_updated() -> None:
    async def run() -> None:
        backend = InMemoryBackend(max_entries=2)
        await backend.set("app:a", b"A", expire=100)
        await backend.set("app:b", b"B", expire=100)
        assert await backend.get("app:a") == b"A"  # LRU: b, a
        await backend.set("app:c", b"C", expire=100)
        assert await backend.get("app:b") is None
        assert await backend.get("app:a") == b"A"
        assert await backend.get("app:c") == b"C"
        # Replacing an existing key refreshes its recency without extra slots.
        await backend.set("app:a", b"A2", expire=None)
        await backend.set("app:d", b"D", expire=None)
        assert await backend.get("app:c") is None
        assert await backend.get("app:a") == b"A2"
        assert await backend.get("app:d") == b"D"
        assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]
    asyncio.run(run())


def test_ttl_reclaims_expired_unvisited_keys_before_eviction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend(max_entries=2)
        await backend.set("n:live", b"keep", expire=50)
        assert await backend.get_with_ttl("n:live") == (50, b"keep")
        # The expiring entry is *newer* than the live one: a naive
        # LRU-only eviction would drop live data and keep the stale key.
        await backend.set("n:expired", b"old", expire=5)
        now[0] = 1006
        await backend.set("n:new", b"new", expire=50)
        assert await backend.get("n:expired") is None
        assert await backend.get("n:live") == b"keep"
        assert await backend.get("n:new") == b"new"
        assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]
    asyncio.run(run())


def test_expire_none_and_scoped_clear_keep_lru_consistent() -> None:
    async def run() -> None:
        backend = InMemoryBackend(max_entries=3)
        await backend.set("app:a:1", b"one", expire=None)
        await backend.set("app:a:2", b"two", expire=None)
        await backend.set("app:ab:3", b"three", expire=None)
        assert await backend.clear(namespace="app:a") == 2
        assert await backend.get("app:ab:3") == b"three"
        await backend.set("app:a:4", b"four", expire=None)
        assert await backend.clear(key="app:ab:3") == 1
        await backend.set("app:a:5", b"five", expire=None)
        await backend.set("app:a:6", b"six", expire=None)
        assert await backend.get_with_ttl("app:a:4") == (-1, b"four")
        assert await backend.get("app:a:5") == b"five"
        assert await backend.get("app:a:6") == b"six"
        assert len(backend._store) == 3  # pyright: ignore[reportPrivateUsage]
    asyncio.run(run())


def test_instances_keep_independent_capacity_and_evictions() -> None:
    async def run() -> None:
        first = InMemoryBackend(max_entries=1)
        second = InMemoryBackend(max_entries=1)
        await first.set("app:a", b"first", expire=None)
        await second.set("app:a", b"second", expire=None)
        await first.set("app:b", b"b", expire=None)
        assert await first.get("app:a") is None
        assert await second.get("app:a") == b"second"
        assert await second.get("app:b") is None
    asyncio.run(run())


def test_concurrent_writes_and_reads_respect_max_entries() -> None:
    async def run() -> None:
        backend = InMemoryBackend(max_entries=7)

        async def write_and_read(i: int) -> None:
            key = "n:" + str(i)
            await backend.set(key, str(i).encode(), expire=60)
            await backend.get_with_ttl(key)

        await asyncio.gather(*(write_and_read(i) for i in range(180)))
        assert len(backend._store) <= 7  # pyright: ignore[reportPrivateUsage]
        assert backend._recency is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._recency) == len(backend._store)  # pyright: ignore[reportPrivateUsage]
        for key in list(backend._store):  # pyright: ignore[reportPrivateUsage]
            assert await backend.get(key) is not None

    asyncio.run(run())


def test_fastapi_http_lru_miss_hit_and_eviction() -> None:
    backend = InMemoryBackend(max_entries=1)
    FastAPICache.init(backend, prefix="http-test")
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/value/{value}")
    @cache(expire=60)
    async def value(value: str) -> Dict[str, str]:
        calls["n"] += 1
        return {"value": value, "count": str(calls["n"])}

    with TestClient(app) as client:
        first = client.get("/value/a")
        hit = client.get("/value/a")
        other = client.get("/value/b")
        evicted = client.get("/value/a")
        assert [r.headers["X-FastAPI-Cache"] for r in
                (first, hit, other, evicted)] == ["MISS", "HIT", "MISS", "MISS"]
        assert first.json() == hit.json()
        assert first.json() != evicted.json()
        assert other.json()["value"] == "b"


def test_expiry_heap_does_not_accumulate_stale_entries_after_overwrites() -> None:
    async def run() -> None:
        backend = InMemoryBackend(max_entries=3)
        for i in range(2000):
            await backend.set("app:repeat", str(i).encode(), expire=3600)
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 1  # pyright: ignore[reportPrivateUsage]
        assert len(backend._store) == 1  # pyright: ignore[reportPrivateUsage]
        await backend.set("app:repeat", b"forever", expire=None)
        assert len(backend._expiry_index) == 0  # pyright: ignore[reportPrivateUsage]
        assert await backend.get("app:repeat") == b"forever"
        await backend.set("app:a", b"a", expire=30)
        await backend.set("app:b", b"b", expire=30)
        await backend.set("app:c", b"c", expire=30)
        assert len(backend._expiry_index) == 3  # pyright: ignore[reportPrivateUsage]
        assert len(backend._store) == 3  # pyright: ignore[reportPrivateUsage]
    asyncio.run(run())


def test_expiration_index_updates_and_clear_delete_correct_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend(max_entries=2)
        await backend.set("app:a", b"a", expire=2)
        await backend.set("app:b", b"b", expire=12)
        # Overwriting changes an existing TTL; old heap record must disappear.
        await backend.set("app:a", b"fresh", expire=100)
        now[0] = 1003
        await backend.set("app:c", b"c", expire=100)
        assert await backend.get("app:a") == b"fresh"
        assert await backend.get("app:b") is None
        assert await backend.get("app:c") == b"c"
        assert await backend.clear(namespace="app") == 2
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 0  # pyright: ignore[reportPrivateUsage]
    asyncio.run(run())


def test_bounded_entries_remain_bounded_during_key_churn() -> None:
    async def run() -> None:
        backend = InMemoryBackend(max_entries=64)
        for i in range(5000):
            await backend.set(f"stress:{i}", b"x", expire=60)
        assert len(backend._store) == 64  # pyright: ignore[reportPrivateUsage]
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 64  # pyright: ignore[reportPrivateUsage]
        assert backend._recency is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._recency) == 64  # pyright: ignore[reportPrivateUsage]
    asyncio.run(run())


def test_expiry_heap_rebalances_upward_after_middle_key_removal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removing a non-tail expiry can move the heap tail above its parent."""
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: 1000)

    async def run() -> None:
        backend = InMemoryBackend(max_entries=7)
        # In insertion order these expire at:
        #         1
        #       10  2
        #      20 30 3 4
        # Removing the 20 moves 4 below 10: it must sift UP, not down.
        for index, ttl in enumerate((1, 10, 2, 20, 30, 3, 4)):
            await backend.set(f"heap:{index}", str(index).encode(), expire=ttl)
        assert await backend.clear(key="heap:3") == 1
        assert await backend.get("heap:3") is None
        assert await backend.get("heap:6") == b"6"
        assert backend._expiry_index is not None  # pyright: ignore[reportPrivateUsage]
        assert len(backend._expiry_index) == 6  # pyright: ignore[reportPrivateUsage]

        # A later expiry reclaim must still select the earliest actual TTL.
        now = 1003  # ttl=1 expired, ttl=4 still valid
        monkeypatch.setattr(
            "fastapi_cache.backends.inmemory.time.time", lambda: now
        )
        await backend.set("heap:new", b"new", expire=30)
        assert await backend.get("heap:0") is None
        assert await backend.get("heap:6") is not None

    asyncio.run(run())

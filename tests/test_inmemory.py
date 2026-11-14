import asyncio
from typing import Dict, Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def test_store_and_lock_are_instance_scoped() -> None:
    first = InMemoryBackend()
    second = InMemoryBackend()

    assert first._store is not second._store  # pyright: ignore[reportPrivateUsage]
    assert first._lock is not second._lock  # pyright: ignore[reportPrivateUsage]


def test_instances_do_not_share_store() -> None:
    async def run() -> None:
        first = InMemoryBackend()
        second = InMemoryBackend()

        await first.set("app:key", b"first", expire=60)
        assert await second.get("app:key") is None

        await second.set("app:key", b"second", expire=60)
        assert await first.get("app:key") == b"first"
        assert await second.get("app:key") == b"second"

    asyncio.run(run())


def test_clear_does_not_affect_other_instances() -> None:
    async def run() -> None:
        first = InMemoryBackend()
        second = InMemoryBackend()

        await first.set("app:key", b"first", expire=60)
        await second.set("app:key", b"second", expire=60)

        assert await first.clear(key="app:key") == 1
        assert await first.get("app:key") is None
        assert await second.get("app:key") == b"second"

    asyncio.run(run())


def test_none_expire_does_not_expire(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend()
        await backend.set("app:key", b"value", expire=None)

        now[0] = 10_000

        assert await backend.get("app:key") == b"value"
        assert await backend.get_with_ttl("app:key") == (-1, b"value")

    asyncio.run(run())


def test_finite_expire_returns_remaining_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    async def run() -> None:
        backend = InMemoryBackend()
        await backend.set("app:key", b"value", expire=60)

        assert await backend.get_with_ttl("app:key") == (60, b"value")

        now[0] = 1030
        assert await backend.get_with_ttl("app:key") == (30, b"value")

        now[0] = 1061
        assert await backend.get_with_ttl("app:key") == (0, None)

    asyncio.run(run())


def test_decorator_default_expire_caches_forever(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])

    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="compat")
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/value")
    @cache()
    async def value() -> Dict[str, int]:  # pyright: ignore[reportUnusedFunction]
        calls["n"] += 1
        return {"n": calls["n"]}

    with TestClient(app) as client:
        first = client.get("/value")
        now[0] = 10_000
        second = client.get("/value")

    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert first.json() == second.json() == {"n": 1}
    assert calls["n"] == 1


def test_new_backend_after_reset_does_not_see_old_entries() -> None:
    first = InMemoryBackend()
    FastAPICache.init(first, prefix="compat")
    asyncio.run(first.set("compat:key", b"value", expire=60))

    FastAPICache.reset()
    second = InMemoryBackend()
    FastAPICache.init(second, prefix="compat")

    assert asyncio.run(second.get("compat:key")) is None

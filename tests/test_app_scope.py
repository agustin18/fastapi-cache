"""Application-scoped C1 contracts; no remote Redis or destructive flush."""

import asyncio
import hashlib
import logging
import os
import sys
import uuid
from dataclasses import FrozenInstanceError
from typing import Any, Dict, Generator, Optional
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi import APIRouter, FastAPI
from starlette.requests import Request

from fastapi_cache import CacheConfig, CacheHandle, CacheScopeError, FastAPICache
from fastapi_cache.app import _SLOT, _physical_key
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi_cache.types import Backend

GOLDEN = (
    "__fastapi_cache_app_v1__:shop-a:"
    "1c168adb00d208e42f93314529f1fa9c0427eb63233ceda95a5db52b7012a719:"
    "d7439bee24773bcbfa2d0a97947ee36227b10d1022b1a55847e928965bb6bfde"
)


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def _request(app: FastAPI) -> Request:
    return Request({"type": "http", "app": app, "method": "GET", "headers": [],
                    "path": "/value", "root_path": ""})


def _config(backend: Backend, scope_id: str, **kwargs: Any) -> CacheConfig:
    return CacheConfig(backend, scope_id=scope_id, expire=60, **kwargs)


def test_golden_and_validation() -> None:
    config = _config(InMemoryBackend(), "shop-a")
    assert _physical_key(config, "orders", "raw") == GOLDEN
    assert _physical_key(config, "", "raw").split(":")[2] == hashlib.sha256(b"").hexdigest()
    assert _physical_key(config, "é", "raw") != _physical_key(config, "e\u0301", "raw")
    assert _physical_key(config, "orders", GOLDEN) != GOLDEN
    other = _config(InMemoryBackend(), "a" * 64)
    assert len(_physical_key(other, "", "raw")) == 219
    with pytest.raises(FrozenInstanceError):
        setattr(config, "scope_id", "changed")  # noqa: B010
    for invalid in ("", "\ud800", 42):
        with pytest.raises(CacheScopeError):
            _physical_key(config, "orders", invalid)  # type: ignore[arg-type]
    with pytest.raises(CacheScopeError):
        cache(scope="app", namespace="\ud800")
    with pytest.raises(CacheScopeError):
        cache(scope="unknown")
    with pytest.raises(CacheScopeError):
        cache(scope="app", handle=CacheHandle(config))
    with pytest.raises(CacheScopeError):
        cache(handle=object())  # type: ignore[arg-type]


@pytest.mark.parametrize("scope_id", ["", "Upper", "a:b", "a*", "a ", "é", "a" * 65, 42])
def test_invalid_scope_never_binds(scope_id: Any) -> None:
    async def verify() -> None:
        app = FastAPI()
        handle = CacheHandle(_config(InMemoryBackend(), scope_id))
        with pytest.raises(CacheScopeError):
            await handle.start(app)
        assert not hasattr(app.state, _SLOT)
        await handle.aclose()

    asyncio.run(verify())


def test_invalid_config_and_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    class Custom(InMemoryBackend):
        pass

    async def verify() -> None:
        app = FastAPI()
        configs = [
            object(),
            _config(InMemoryBackend(), "a", prefix="\ud800"),
            _config(InMemoryBackend(), "a", enable=None),
            _config(Custom(), "a"),
        ]
        for config in configs:
            with pytest.raises(CacheScopeError):
                await CacheHandle(config).start(app)  # type: ignore[arg-type]
            assert not hasattr(app.state, _SLOT)
        monkeypatch.setitem(sys.modules, "fastapi_cache.backends.redis", None)
        with pytest.raises(CacheScopeError):
            await CacheHandle(_config(Custom(), "a")).start(app)

    asyncio.run(verify())


def test_resolution_rejects_missing_conflict_foreign_closed_and_direct() -> None:
    async def verify() -> None:
        a, b = FastAPI(), FastAPI()
        config = _config(InMemoryBackend(), "a")
        first, second = CacheHandle(config), CacheHandle(_config(InMemoryBackend(), "b"))
        direct: Any = cache(scope="app")(lambda: 1)
        explicit: Any = cache(handle=first)(lambda: 2)

        with pytest.raises(CacheScopeError):
            await direct()
        with pytest.raises(CacheScopeError):
            await direct(__fastapi_cache_request=Request({"type": "http"}))
        with pytest.raises(CacheScopeError):
            await direct(__fastapi_cache_request=_request(a))
        with pytest.raises(CacheScopeError):
            await first.start(object())  # type: ignore[arg-type]
        await first.start(a)
        with pytest.raises(CacheScopeError):
            await first.start(a)
        with pytest.raises(CacheScopeError):
            await second.start(a)
        await second.start(b)
        with pytest.raises(CacheScopeError):
            await explicit(__fastapi_cache_request=_request(b))
        # A copied slot is not a binding, even while the original app is live.
        setattr(b.state, _SLOT, first)
        with pytest.raises(CacheScopeError):
            await direct(__fastapi_cache_request=_request(b))
        setattr(b.state, _SLOT, second)
        assert await explicit(__fastapi_cache_request=_request(a)) == 2
        await first.aclose()
        await first.aclose()
        with pytest.raises(CacheScopeError):
            await explicit(__fastapi_cache_request=_request(a))
        with pytest.raises(CacheScopeError):
            await first.clear()
        await second.aclose()
        replacement = CacheHandle(config)
        await replacement.start(a)
        with pytest.raises(CacheScopeError):
            await explicit(__fastapi_cache_request=_request(a))
        await replacement.aclose()
        assert not hasattr(a.state, _SLOT)

    asyncio.run(verify())


async def _exercise_shared_store(backend: Backend, first_id: str, second_id: str) -> None:
    a, b = FastAPI(), FastAPI()
    calls = {"a": 0, "b": 0}
    foreign = _physical_key(_config(backend, second_id), "orders", "raw")

    async def hostile(*args: Any, **kwargs: Any) -> str:
        return foreign

    def install(app: FastAPI, name: str) -> None:
        @app.get("/value")
        @cache(scope="app", namespace="orders", vary_headers=["X-Region"])
        async def value() -> Dict[str, Any]:
            calls[name] += 1
            return {"app": name, "count": calls[name]}

        @app.get("/other")
        @cache(scope="app", namespace="")
        async def other() -> Dict[str, str]:
            return {"app": name}

    install(a, "a")
    install(b, "b")
    ha = CacheHandle(_config(backend, first_id, key_builder=hostile,
                             cache_status_header="X-App-A"))
    hb = CacheHandle(_config(backend, second_id, key_builder=hostile,
                             cache_status_header="X-App-B"))
    await ha.start(a)
    await hb.start(b)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=a),
                                     base_url="http://app.test") as ca, httpx.AsyncClient(
            transport=httpx.ASGITransport(app=b), base_url="http://app.test"
        ) as cb:
            first, second = await asyncio.gather(ca.get("/value"), cb.get("/value"))
            assert first.json() == {"app": "a", "count": 1}
            assert second.json() == {"app": "b", "count": 1}
            assert first.headers["X-App-A"] == second.headers["X-App-B"] == "MISS"
            FastAPICache.init(InMemoryBackend(), enable=False, force=True)
            assert (await ca.get("/value")).headers["X-App-A"] == "HIT"
            FastAPICache.reset()
            assert (await cb.get("/value")).headers["X-App-B"] == "HIT"
            varied = await ca.get("/value", headers={"X-Region": "east"})
            assert varied.headers["X-App-A"] == "MISS"
            assert varied.json()["count"] == 2
            conditional = await ca.get("/value", headers={"If-None-Match": first.headers["ETag"]})
            assert conditional.status_code == 304
            assert (await ca.get("/other")).headers["X-App-A"] == "MISS"
            assert await backend.get(foreign) is None
            with pytest.raises(CacheScopeError):
                await ha.clear(key=foreign)
            own = _physical_key(_config(backend, first_id), "", foreign)
            assert await ha.clear(key=own) == 1
            assert (await ca.get("/other")).headers["X-App-A"] == "MISS"
            assert await ha.clear(namespace="") == 1
            assert await ha.clear(namespace="orders") == 2
            assert (await cb.get("/value")).headers["X-App-B"] == "HIT"
            assert (await ca.get("/value")).headers["X-App-A"] == "MISS"
            assert await ha.clear() == 1
            await ha.aclose()
            assert (await cb.get("/value")).headers["X-App-B"] == "HIT"
    finally:
        # Cleanup even if an assertion fails after one handle has closed.
        for h, sid in ((ha, first_id), (hb, second_id)):
            await backend.clear(namespace="__fastapi_cache_app_v1__:" + sid)
            await h.aclose()


def test_two_apps_shared_inmemory() -> None:
    asyncio.run(_exercise_shared_store(InMemoryBackend(), "shop-a", "shop-ab"))


@pytest.mark.redis
def test_two_apps_shared_real_redis() -> None:
    url = os.environ.get("REDIS_URL")
    if not url:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("Redis integration requires REDIS_URL")
        pytest.skip("Redis integration requires REDIS_URL")
    if urlsplit(url).hostname not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail("Refusing non-loopback Redis")
    from redis.asyncio import Redis

    from fastapi_cache.backends.redis import RedisBackend

    async def verify() -> None:
        client = Redis.from_url(url, decode_responses=False)
        backend = RedisBackend(client)
        try:
            backend.is_cluster = True
            with pytest.raises(CacheScopeError):
                await CacheHandle(_config(backend, "cluster")).start(FastAPI())
            backend.is_cluster = False
            scope = "c1-" + uuid.uuid4().hex
            await _exercise_shared_store(backend, scope, scope + "-b")
            # Successful ping alone could reconnect; also spy that cache did
            # not call the client's close or disconnect methods below.
            assert await client.ping()
        finally:
            closer = getattr(client, "aclose", None)
            if closer is None:
                closer = client.close
            await closer()

    asyncio.run(verify())


def test_mount_shared_router_and_legacy_default() -> None:
    async def verify() -> None:
        parent, child = FastAPI(), FastAPI()
        router = APIRouter()

        @router.get("/scoped")
        @cache(scope="app")
        async def scoped() -> str:
            return "scoped"

        @router.get("/legacy")
        @cache()
        async def legacy() -> str:
            return "legacy"

        parent.include_router(router)
        child.include_router(router)
        parent.mount("/child", child)
        store = InMemoryBackend()
        p = CacheHandle(_config(store, "parent", cache_status_header="X-Parent"))
        c = CacheHandle(_config(store, "child", cache_status_header="X-Child", enable=False))
        FastAPICache.init(InMemoryBackend(), cache_status_header="X-Legacy")
        await p.start(parent)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=parent),
                                         base_url="http://app.test") as http:
                with pytest.raises(CacheScopeError):
                    await http.get("/child/scoped")
                await c.start(child)
                assert (await http.get("/scoped")).headers["X-Parent"] == "MISS"
                assert (await http.get("/scoped")).headers["X-Parent"] == "HIT"
                assert "X-Child" not in (await http.get("/child/scoped")).headers
                assert (await http.get("/child/legacy")).headers["X-Legacy"] == "MISS"
                assert (await http.get("/child/legacy")).headers["X-Legacy"] == "HIT"
                await c.aclose()
                with pytest.raises(CacheScopeError):
                    await http.get("/child/scoped")
        finally:
            await p.aclose()

    asyncio.run(verify())


def test_invalid_clear_and_foreign_binding() -> None:
    async def verify() -> None:
        app = FastAPI()
        handle = CacheHandle(_config(InMemoryBackend(), "shop-a"))
        await handle.start(app)
        for key in ("", "raw", GOLDEN + ":extra", GOLDEN.upper(), GOLDEN.replace("shop-a", "shop-ab"), 42):
            with pytest.raises(CacheScopeError):
                await handle.clear(key=key)  # type: ignore[arg-type]
        with pytest.raises(CacheScopeError):
            await handle.clear(key=GOLDEN, namespace="")
        with pytest.raises(CacheScopeError):
            await handle.clear(namespace="\ud800")
        setattr(app.state, _SLOT, None)
        with pytest.raises(CacheScopeError):
            await handle.clear()
        with pytest.raises(CacheScopeError):
            await handle.aclose()
        assert getattr(app.state, _SLOT) is None

    asyncio.run(verify())


def test_drain_timeout_cancellation_and_wrong_loop() -> None:
    async def verify() -> None:
        app = FastAPI()
        handle = CacheHandle(_config(InMemoryBackend(), "drain"))
        await handle.start(app)
        entered, release = asyncio.Event(), asyncio.Event()

        @app.get("/blocked")
        @cache(scope="app")
        async def blocked() -> str:
            entered.set()
            await release.wait()
            return "done"

        async def wrong_loop() -> None:
            with pytest.raises(CacheScopeError):
                await handle.clear()
            with pytest.raises(CacheScopeError):
                await handle.aclose()

        await asyncio.get_running_loop().run_in_executor(None, lambda: asyncio.run(wrong_loop()))
        for timeout in (0, -1, float("inf"), float("nan"), True, "1"):
            with pytest.raises(CacheScopeError):
                await handle.aclose(timeout=timeout)  # type: ignore[arg-type]
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://app.test") as client:
            task = asyncio.create_task(client.get("/blocked"))
            await asyncio.wait_for(entered.wait(), 5)
            with pytest.raises(asyncio.TimeoutError):
                await handle.aclose(timeout=0.001)
            assert getattr(app.state, _SLOT) is handle
            with pytest.raises(CacheScopeError):
                await client.get("/blocked")
            waiter = asyncio.create_task(handle.aclose())
            other = asyncio.create_task(handle.aclose())
            await asyncio.sleep(0)
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiter
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            await asyncio.wait_for(other, 5)
            assert not hasattr(app.state, _SLOT)
            await handle.aclose()

    asyncio.run(verify())


def test_drain_allows_admitted_request_and_clear() -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        app = FastAPI()
        handle = CacheHandle(_config(backend, "drain"))
        await handle.start(app)
        entered, release = asyncio.Event(), asyncio.Event()

        @app.get("/blocked")
        @cache(scope="app")
        async def blocked() -> str:
            entered.set()
            await release.wait()
            return "done"

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://app.test") as client:
            task = asyncio.create_task(client.get("/blocked"))
            await asyncio.wait_for(entered.wait(), 5)
            closer = asyncio.create_task(handle.aclose())
            await asyncio.sleep(0)
            assert not closer.done()
            with pytest.raises(CacheScopeError):
                await handle.clear()
            release.set()
            assert (await asyncio.wait_for(task, 5)).json() == "done"
            await asyncio.wait_for(closer, 5)
        assert not hasattr(app.state, _SLOT)

    asyncio.run(verify())


@pytest.mark.parametrize("bad", ["", "\ud800", 42])
def test_bad_builder_never_accesses_backend(bad: Any) -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        app = FastAPI()

        def builder(*args: Any, **kwargs: Any) -> Any:
            return bad

        handle = CacheHandle(_config(backend, "bad", key_builder=builder))
        await handle.start(app)
        endpoint: Any = cache(scope="app", vary_headers=["X-Region"])(lambda: "bad")
        with pytest.raises(CacheScopeError):
            await endpoint(__fastapi_cache_request=_request(app))
        assert not backend._store
        await handle.aclose()

    asyncio.run(verify())


def test_scoped_privacy_and_backend_failure_redaction(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        app = FastAPI()

        async def fail(*args: Any, **kwargs: Any) -> Any:
            raise ConnectionError("synthetic-secret")

        monkeypatch.setattr(backend, "get_with_ttl", fail)
        monkeypatch.setattr(backend, "set", fail)
        handle = CacheHandle(_config(backend, "redaction"))
        await handle.start(app)

        @app.get("/value")
        @cache(scope="app", namespace="synthetic-private-namespace")
        async def value() -> str:
            return "public"

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://app.test") as client:
            with caplog.at_level(logging.WARNING):
                assert (await client.get("/value")).headers["X-FastAPI-Cache"] == "MISS"
                authenticated = await client.get("/value", headers={"Authorization": "Bearer synthetic"})
                assert "X-FastAPI-Cache" not in authenticated.headers
        assert "ConnectionError" in caplog.text
        assert "synthetic-secret" not in caplog.text
        assert "synthetic-private-namespace" not in caplog.text
        await handle.aclose()

    asyncio.run(verify())

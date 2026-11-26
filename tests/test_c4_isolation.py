"""C4 end-to-end scope/identity/migration evidence using synthetic data."""

import asyncio
import hashlib
import json
import multiprocessing
import os
import uuid
from contextvars import ContextVar
from typing import Any, Dict
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi import Depends, FastAPI, Header, Request

from fastapi_cache import CacheConfig, CacheFailurePolicy, CacheHandle, FastAPICache
from fastapi_cache.app import _physical_key
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi_cache.types import Backend

_IDENTITY: ContextVar[str] = ContextVar("synthetic_c4_identity", default="")


def _identity_key(*args: Any, **kwargs: Any) -> str:
    request = kwargs["request"]
    identity = request.state.identity
    # Synthetic authorization model; production must validate credentials and
    # include all response dimensions. Structured encoding avoids ambiguity.
    material = json.dumps([identity, request.url.path], separators=(",", ":"))
    return hashlib.sha256(material.encode()).hexdigest()


def _constant(*args: Any, **kwargs: Any) -> str:
    return "synthetic-shared-key"


def _make_app(name: str) -> FastAPI:
    app = FastAPI()

    async def authorize(request: Request) -> None:
        # Deliberately synthetic credentials, validated before decorator lookup.
        token = request.headers.get("Authorization", "")
        identities = {"Bearer synthetic-a": "alice", "Bearer synthetic-b": "bob"}
        from fastapi import HTTPException

        if token not in identities:
            raise HTTPException(status_code=403)
        request.state.identity = identities[token]

    @app.get("/private", dependencies=[Depends(authorize)])
    @cache(scope="app", namespace="private", cache_authenticated=True,
           key_builder=_identity_key, vary_headers=["Accept-Language"])
    async def private(request: Request, language: str = Header(
        default="en", alias="Accept-Language"
    )) -> Dict[str, str]:
        return {"app": name, "identity": request.state.identity, "language": language}

    @app.get("/public")
    @cache(scope="app", namespace="public", key_builder=_constant)
    async def public() -> Dict[str, str]:
        return {"app": name}

    return app


async def _exercise(backend: Backend, scope: str) -> None:
    a, b = _make_app("a"), _make_app("b")
    ha = CacheHandle(CacheConfig(
        backend, scope_id=scope, expire=60,
        failure_policy=CacheFailurePolicy(True, True, True),
    ))
    hb = CacheHandle(CacheConfig(backend, scope_id=scope + "-b", expire=60))
    await ha.start(a)
    await hb.start(b)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=a), base_url="http://test"
        ) as ca, httpx.AsyncClient(
            transport=httpx.ASGITransport(app=b), base_url="http://test"
        ) as cb:
            clients = [(ca, "a"), (cb, "b")]

            async def verify(client: httpx.AsyncClient, name: str, token: str,
                             identity: str, locale: str) -> None:
                headers = {"Authorization": token, "Accept-Language": locale}
                first = await client.get("/private", headers=headers)
                hit = await client.get("/private", headers=headers)
                assert first.status_code == hit.status_code == 200
                assert first.headers["X-FastAPI-Cache"] == "MISS"
                assert hit.headers["X-FastAPI-Cache"] == "HIT"
                assert hit.json() == first.json() == {
                    "app": name, "identity": identity, "language": locale,
                }
                assert hit.headers["Cache-Control"] == "private, no-store"
                assert hit.headers["Vary"] == "accept-language"
                conditional = await client.get(
                    "/private", headers={**headers, "If-None-Match": hit.headers["ETag"]}
                )
                assert conditional.status_code == 304
                assert conditional.headers["Cache-Control"] == "private, no-store"

            await asyncio.gather(*(
                verify(client, name, token, identity, locale)
                for client, name in clients
                for token, identity in (
                    ("Bearer synthetic-a", "alice"), ("Bearer synthetic-b", "bob")
                )
                for locale in ("en", "es")
            ))
            for client, name in clients:
                denied = await client.get("/private", headers={"Authorization": "invalid"})
                assert denied.status_code == 403
                assert "X-FastAPI-Cache" not in denied.headers
                assert (await client.get("/public")).json() == {"app": name}
            # Existing legacy keys are not interpreted as scoped entries.
            legacy_key = scope + ":legacy"
            await backend.set(legacy_key, b'"legacy"', expire=60)
            assert await ha.clear() == 5
            assert await backend.get(legacy_key) == b'"legacy"'
            assert (await cb.get("/public")).headers["X-FastAPI-Cache"] == "HIT"
            result = await ca.get("/public")
            assert result.headers["X-FastAPI-Cache"] == "MISS"
            assert result.json() == {"app": "a"}
            await backend.clear(key=legacy_key)
    finally:
        for handle in (ha, hb):
            await handle.clear()
            await handle.aclose()


def test_inmemory_identity_scope_matrix() -> None:
    asyncio.run(_exercise(InMemoryBackend(), "c4-memory"))


def test_hidden_context_remains_application_responsibility() -> None:
    async def verify() -> None:
        app = FastAPI()
        store = InMemoryBackend()
        handle = CacheHandle(CacheConfig(store, scope_id="hidden", expire=60))
        await handle.start(app)

        async def choose(request: Request) -> None:
            _IDENTITY.set(request.headers.get("X-Synthetic-Tenant", ""))

        @app.get("/unsafe", dependencies=[Depends(choose)])
        @cache(scope="app")
        async def unsafe() -> str:
            return _IDENTITY.get()

        @app.get("/safe", dependencies=[Depends(choose)])
        @cache(scope="app", vary_headers=["X-Synthetic-Tenant"])
        async def safe() -> str:
            return _IDENTITY.get()

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                first = await client.get("/unsafe", headers={"X-Synthetic-Tenant": "a"})
                second = await client.get("/unsafe", headers={"X-Synthetic-Tenant": "b"})
                assert first.json() == second.json() == "a"
                assert second.headers["X-FastAPI-Cache"] == "HIT"
                for tenant in ("a", "b", "a", "b"):
                    result = await client.get("/safe", headers={"X-Synthetic-Tenant": tenant})
                    assert result.json() == tenant
        finally:
            await handle.aclose()

    asyncio.run(verify())


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("Redis C4 requires REDIS_URL")
        pytest.skip("Redis C4 requires REDIS_URL")
    assert url is not None
    parsed = urlsplit(url)
    if (parsed.scheme != "redis" or parsed.hostname not in ("localhost", "127.0.0.1", "::1")
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        pytest.fail("Refusing non-loopback or credential-bearing Redis")
    return url


@pytest.mark.redis
def test_real_redis_identity_scope_matrix() -> None:
    from redis.asyncio import Redis

    from fastapi_cache.backends.redis import RedisBackend

    url = _redis_url()

    async def verify() -> None:
        client = Redis.from_url(url, decode_responses=False)
        scope = "c4-" + uuid.uuid4().hex
        backend = RedisBackend(client)
        try:
            await _exercise(backend, scope)
        finally:
            for sid in (scope, scope + "-b"):
                await backend.clear(namespace="__fastapi_cache_app_v1__:" + sid)
            await backend.clear(key=scope + ":legacy")
            closer = getattr(client, "aclose", None)
            if closer is None:
                closer = client.close
            await closer()

    asyncio.run(verify())


def _worker(url: str, scope: str, expected: str, name: str) -> None:
    """Spawned process: own interpreter, event loop, client and handle."""
    from redis.asyncio import Redis

    from fastapi_cache.backends.redis import RedisBackend

    async def verify() -> None:
        redis = Redis.from_url(url, decode_responses=False)
        app = _make_app(name)
        config = CacheConfig(RedisBackend(redis), scope_id=scope, expire=60)
        handle = CacheHandle(config)
        await handle.start(app)
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/public")
                assert response.json() == {"app": expected}
                assert response.headers["X-FastAPI-Cache"] == ("HIT" if expected != name else "MISS")
        finally:
            await handle.aclose()
            closer = getattr(redis, "aclose", None)
            if closer is None:
                closer = redis.close
            await closer()

    asyncio.run(verify())


@pytest.mark.redis
def test_cross_process_scope_reuse_and_separation() -> None:
    from redis.asyncio import Redis

    from fastapi_cache.backends.redis import RedisBackend

    url = _redis_url()
    scope = "c4-workers-" + uuid.uuid4().hex
    ctx = multiprocessing.get_context("spawn")
    try:
        # Same logical app ID deliberately reuses the entry across fresh
        # processes; a different app ID sharing that Redis cannot read it.
        for sid, expected, name in (
            (scope, "first", "first"),
            (scope, "first", "second"),
            (scope + "-b", "other", "other"),
        ):
            process = ctx.Process(target=_worker, args=(url, sid, expected, name))
            process.start()
            try:
                process.join(20)
                assert process.exitcode == 0
            finally:
                if process.is_alive():
                    process.terminate()
                    process.join(5)
                process.close()
    finally:
        async def cleanup() -> None:
            redis = Redis.from_url(url, decode_responses=False)
            backend = RedisBackend(redis)
            try:
                for sid in (scope, scope + "-b"):
                    await backend.clear(namespace="__fastapi_cache_app_v1__:" + sid)
            finally:
                closer = getattr(redis, "aclose", None)
                if closer is None:
                    closer = redis.close
                await closer()

        asyncio.run(cleanup())


def test_opt_in_rollback_keeps_legacy_bytes_and_keys() -> None:
    async def verify() -> None:
        store = InMemoryBackend()
        app = FastAPI()
        FastAPICache.reset()
        FastAPICache.init(store, key_builder=_constant, expire=60)
        legacy = _constant()
        await store.set(legacy, b'"old"', expire=60)
        config = CacheConfig(store, scope_id="migration", key_builder=_constant, expire=60)
        handle = CacheHandle(config)
        await handle.start(app)

        @app.get("/legacy")
        @cache()
        async def old() -> str:
            return "unexpected"

        @app.get("/scoped")
        @cache(scope="app")
        async def new() -> str:
            return "new"

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                assert (await client.get("/legacy")).json() == "old"
                assert (await client.get("/scoped")).json() == "new"
                assert await store.get(_physical_key(config, "", legacy)) == b'"new"'
                await handle.clear()
                await handle.aclose()
                assert await store.get(legacy) == b'"old"'
                result = await client.get("/legacy")
                assert result.json() == "old"
                assert result.headers["X-FastAPI-Cache"] == "HIT"
        finally:
            await handle.aclose()
            FastAPICache.reset()

    asyncio.run(verify())

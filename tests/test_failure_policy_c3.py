"""C3 opt-in policy; synthetic data and disposable loopback Redis only."""

import asyncio
import json
import logging
import os
import pickle
import uuid
from dataclasses import FrozenInstanceError
from typing import Any, Dict, Type
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi import FastAPI, Response
from pydantic import BaseModel, ValidationError
from starlette.responses import JSONResponse

from fastapi_cache import (
    CacheBackendReadError,
    CacheConfig,
    CacheFailurePolicy,
    CacheHandle,
    CacheScopeError,
    JsonCoder,
    TypedJsonCoder,
)
from fastapi_cache.app import _physical_key
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.coder import Coder, PickleCoder
from fastapi_cache.decorator import _etag_for, cache


def _key(*args: Any, **kwargs: Any) -> str:
    return "synthetic-key"


def test_policy_validation() -> None:
    policy = CacheFailurePolicy()
    assert not policy.strict_read
    assert not policy.conservative_write
    assert not policy.recover_json
    with pytest.raises(FrozenInstanceError):
        setattr(policy, "recover_json", True)  # noqa: B010
    with pytest.raises(ValueError, match="Cache failure policy flags must be bool"):
        CacheFailurePolicy(recover_json=1)  # type: ignore[arg-type]

    async def verify() -> None:
        config = CacheConfig(InMemoryBackend(), scope_id="bad", failure_policy=None)  # type: ignore[arg-type]
        with pytest.raises(CacheScopeError):
            await CacheHandle(config).start(FastAPI())

    asyncio.run(verify())


@pytest.mark.parametrize("coder", [JsonCoder, TypedJsonCoder])
@pytest.mark.parametrize("payload", [b"{", b"\xff", b""])
def test_corruption_is_opt_in_no_write_no_304(
    coder: Type[Coder], payload: bytes, caplog: pytest.LogCaptureFixture
) -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        app = FastAPI()
        calls = []

        @app.get("/value")
        @cache(scope="app")
        async def value() -> Dict[str, int]:
            calls.append(1)
            return {"count": len(calls)}

        for enabled in (False, True):
            config = CacheConfig(
                backend, scope_id="test", key_builder=_key, coder=coder,
                failure_policy=CacheFailurePolicy(recover_json=enabled),
            )
            handle = CacheHandle(config)
            await handle.start(app)
            key = _physical_key(config, "", _key())
            await backend.set(key, payload)
            try:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    headers = {"If-None-Match": _etag_for(payload)}
                    if not enabled:
                        with pytest.raises((json.JSONDecodeError, UnicodeDecodeError)):
                            await client.get("/value", headers=headers)
                        assert calls == []
                    else:
                        with caplog.at_level(logging.WARNING):
                            result = await client.get("/value", headers=headers)
                            again = await client.get("/value", headers={"If-None-Match": "*"})
                        assert result.status_code == again.status_code == 200
                        assert result.json() == {"count": 1}
                        assert again.json() == {"count": 2}
                        assert result.headers["Cache-Control"] == "no-store"
                        assert result.headers["X-FastAPI-Cache"] == "MISS"
                        assert "etag" not in result.headers
                        assert "Cache decode failed (invalid-json)" in caplog.text
                    assert await backend.get(key) == payload
            finally:
                await handle.aclose()

    asyncio.run(verify())


class Model(BaseModel):
    count: int


class CustomJson(JsonCoder):
    @classmethod
    def decode(cls, value: bytes) -> Any:
        raise json.JSONDecodeError("synthetic-custom", "x", 0)


@pytest.mark.parametrize(
    ("coder", "payload", "error"),
    [
        (CustomJson, b"{", json.JSONDecodeError),
        (PickleCoder, b"not-a-pickle", pickle.UnpicklingError),
        (JsonCoder, b'{"__fastapi_cache_spec_type__":"unknown","val":"x"}', TypeError),
        (TypedJsonCoder, b'{"count":"not-an-int"}', ValidationError),
    ],
)
def test_non_syntax_failures_propagate(
    coder: Type[Coder], payload: bytes, error: Type[Exception]
) -> None:
    if coder is TypedJsonCoder:
        pytest.importorskip("pydantic", minversion="2")
    async def verify() -> None:
        backend = InMemoryBackend()
        config = CacheConfig(
            backend, scope_id="test", coder=coder, key_builder=_key,
            failure_policy=CacheFailurePolicy(recover_json=True),
        )
        app = FastAPI()
        handle = CacheHandle(config)
        await handle.start(app)
        calls = []

        @app.get("/value")
        @cache(scope="app")
        async def value() -> Model:
            calls.append(1)
            return Model(count=1)

        key = _physical_key(config, "", _key())
        await backend.set(key, payload)
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                with pytest.raises(error):
                    await client.get("/value", headers={"If-None-Match": "*"})
            assert not calls
            assert await backend.get(key) == payload
        finally:
            await handle.aclose()

    asyncio.run(verify())


@pytest.mark.parametrize("returned", [False, True])
@pytest.mark.parametrize("failure", ["decode", "write"])
def test_degraded_headers_preserve_application_metadata(
    returned: bool, failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        config = CacheConfig(
            backend, scope_id="test", key_builder=_key,
            cache_authenticated=True,
            failure_policy=CacheFailurePolicy(recover_json=True, conservative_write=True),
        )
        app = FastAPI()
        handle = CacheHandle(config)
        await handle.start(app)
        calls = []

        @app.get("/value")
        @cache(scope="app", vary_headers=["X-Region"])
        async def value(response: Response) -> Any:
            calls.append(1)
            if returned:
                # A simple JSONResponse remains encodable; failure must
                # attach metadata to the actual returned response.
                result = JSONResponse({"safe": True})
            else:
                result = {"safe": True}
            if failure == "decode":
                target = result if isinstance(result, Response) else response
                target.headers["ETag"] = '"application-validator"'
                target.headers["Cache-Control"] = "no-cache"
                target.headers["Vary"] = "Accept-Language"
            return result

        async def read(*args: Any, **kwargs: Any) -> Any:
            return (60, b"{") if failure == "decode" else (0, None)

        async def write(*args: Any, **kwargs: Any) -> None:
            raise TimeoutError("synthetic-secret")

        monkeypatch.setattr(backend, "get_with_ttl", read)
        monkeypatch.setattr(backend, "set", write)
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                result = await client.get("/value", headers={
                    "If-None-Match": "*", "Authorization": "Bearer synthetic",
                    "X-Region": "east",
                })
                assert result.status_code == 200
                assert result.json() == {"safe": True}
                assert "no-store" in result.headers["Cache-Control"]
                assert "private" in result.headers["Cache-Control"]
                assert result.headers["X-FastAPI-Cache"] == "MISS"
                if failure == "decode":
                    assert result.headers["ETag"] == '"application-validator"'
                    assert result.headers["Vary"] == "Accept-Language"
                    assert "no-cache" in result.headers["Cache-Control"]
                else:
                    assert "etag" not in result.headers
                    assert result.headers["Vary"] == "x-region"
                    assert "max-age" not in result.headers["Cache-Control"]
                assert calls == [1]
        finally:
            await handle.aclose()

    asyncio.run(verify())


def test_concurrent_recovery_does_not_overwrite_fresh_entry() -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        config = CacheConfig(
            backend, scope_id="test", key_builder=_key,
            failure_policy=CacheFailurePolicy(recover_json=True),
        )
        handle = CacheHandle(config)
        app = FastAPI()
        await handle.start(app)
        entered, release = asyncio.Event(), asyncio.Event()
        calls = []

        @app.get("/value")
        @cache(scope="app")
        async def value() -> str:
            calls.append(1)
            if len(calls) == 2:
                entered.set()
            await release.wait()
            return "computed"

        key = _physical_key(config, "", _key())
        await backend.set(key, b"{")
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                first = asyncio.create_task(client.get("/value"))
                second = asyncio.create_task(client.get("/value"))
                try:
                    await asyncio.wait_for(entered.wait(), 5)
                    await backend.set(key, b'"fresh"')
                finally:
                    release.set()
                    results = await asyncio.gather(first, second)
                assert [r.json() for r in results] == ["computed", "computed"]
                assert await backend.get(key) == b'"fresh"'
                hit = await client.get("/value")
                assert hit.json() == "fresh"
                assert hit.headers["X-FastAPI-Cache"] == "HIT"
                assert len(calls) == 2
        finally:
            await handle.aclose()

    asyncio.run(verify())


@pytest.mark.parametrize("stage", ["read", "write", "recompute"])
def test_cancellation_propagates_and_drain_finishes(
    stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        config = CacheConfig(
            backend, scope_id="test", key_builder=_key,
            failure_policy=CacheFailurePolicy(True, True, True),
        )
        app = FastAPI()
        handle = CacheHandle(config)
        await handle.start(app)
        entered = asyncio.Event()

        async def blocked(*args: Any, **kwargs: Any) -> Any:
            entered.set()
            await asyncio.Event().wait()

        @app.get("/value")
        @cache(scope="app")
        async def value() -> str:
            if stage == "recompute":
                await blocked()
            return "value"

        if stage == "read":
            monkeypatch.setattr(backend, "get_with_ttl", blocked)
        elif stage == "write":
            monkeypatch.setattr(backend, "set", blocked)
        else:
            await backend.set(_physical_key(config, "", _key()), b"{")
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                task = asyncio.create_task(client.get("/value"))
                await asyncio.wait_for(entered.wait(), 5)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
        finally:
            await handle.aclose(timeout=5)

    asyncio.run(verify())


def test_opt_in_unclassified_read_fallback_and_redaction(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    async def verify() -> None:
        backend = InMemoryBackend()
        config = CacheConfig(
            backend, scope_id="test", key_builder=_key,
            failure_policy=CacheFailurePolicy(strict_read=True),
        )
        app = FastAPI()
        handle = CacheHandle(config)
        await handle.start(app)

        async def fail(*args: Any, **kwargs: Any) -> Any:
            raise ValueError("synthetic-secret")

        monkeypatch.setattr(backend, "get_with_ttl", fail)

        @app.get("/value")
        @cache(scope="app", namespace="synthetic-private")
        async def value() -> int:
            return 1

        try:
            with caplog.at_level(logging.WARNING):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    assert (await client.get("/value")).json() == 1
            assert "Cache read failed (unclassified)" in caplog.text
            assert "synthetic-secret" not in caplog.text
            assert "synthetic-private" not in caplog.text
        finally:
            await handle.aclose()

    asyncio.run(verify())


@pytest.mark.redis
def test_real_redis_strict_and_corruption(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    url = os.environ.get("REDIS_URL")
    if not url:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("Redis C3 requires REDIS_URL")
        pytest.skip("Redis C3 requires REDIS_URL")
    assert url is not None
    if urlsplit(url).hostname not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail("Refusing non-loopback Redis")
    from redis.asyncio import Redis
    from redis.exceptions import AuthenticationError
    from redis.exceptions import ConnectionError as RedisConnectionError
    from redis.exceptions import TimeoutError as RedisTimeoutError

    from fastapi_cache.backends.redis import RedisBackend

    async def verify() -> None:
        redis = Redis.from_url(url, decode_responses=False)
        backend = RedisBackend(redis)
        config = CacheConfig(
            backend, scope_id="c3-" + uuid.uuid4().hex, key_builder=_key,
            failure_policy=CacheFailurePolicy(True, True, True),
        )
        app = FastAPI()
        handle = CacheHandle(config)
        await handle.start(app)
        calls = []

        @app.get("/value")
        @cache(scope="app")
        async def value() -> str:
            calls.append(1)
            return "computed"

        key = _physical_key(config, "", _key())
        try:
            await backend.set(key, b"{")
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                assert (await client.get("/value", headers={"If-None-Match": "*"})).json() == "computed"
                assert await backend.get(key) == b"{"
                for error in (RedisConnectionError, RedisTimeoutError, AuthenticationError):
                    async def read(*args: Any, exc_type: Type[Exception] = error, **kwargs: Any) -> Any:
                        raise exc_type("synthetic-secret")

                    with monkeypatch.context() as patch:
                        patch.setattr(backend, "get_with_ttl", read)
                        with caplog.at_level(logging.WARNING):
                            if error is AuthenticationError:
                                assert (await client.get("/value")).json() == "computed"
                            else:
                                with pytest.raises(CacheBackendReadError) as caught:
                                    await client.get("/value")
                                assert caught.value.__context__ is None
                    assert "synthetic-secret" not in caplog.text
                assert len(calls) == 2
                original_set = backend.set
                await handle.clear()
                writes = []

                async def uncertain(*args: Any, **kwargs: Any) -> None:
                    writes.append(1)
                    await original_set(*args, **kwargs)
                    raise RedisTimeoutError("synthetic-committed")

                with monkeypatch.context() as patch:
                    patch.setattr(backend, "set", uncertain)
                    result = await client.get("/value", headers={"If-None-Match": "*"})
                assert result.status_code == 200
                assert result.headers["Cache-Control"] == "no-store"
                assert "etag" not in result.headers
                assert writes == [1]
                assert await backend.get(key) == b'"computed"'
                assert (await client.get("/value")).headers["X-FastAPI-Cache"] == "HIT"
        finally:
            await handle.clear()
            await handle.aclose()
            closer = getattr(redis, "aclose", None)
            if closer is None:
                closer = redis.close
            await closer()

    asyncio.run(verify())

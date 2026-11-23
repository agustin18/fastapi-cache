"""Characterize cache error boundaries without changing the public policy.

All identifiers are synthetic. The only Redis integration uses a loopback,
test-owned key and caller-owned client; no FLUSHDB or production Redis.
"""

import asyncio
import logging
import os
import uuid
from typing import Dict, Generator, Optional, Tuple
from urllib.parse import urlsplit

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.coder import JsonCoder
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


class ReadFailure(InMemoryBackend):
    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        raise ConnectionError("synthetic-confidential-error-detail")


class WriteFailure(InMemoryBackend):
    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        raise TimeoutError("synthetic-sensitive-write-detail")


class CancelledRead(InMemoryBackend):
    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        raise asyncio.CancelledError


class BrokenEncoder(JsonCoder):
    @classmethod
    def encode(cls, value: object) -> bytes:
        raise ValueError("synthetic-coder-failure")


def _app() -> Tuple[FastAPI, Dict[str, int]]:
    app = FastAPI()
    calls = {"count": 0}

    @app.get("/public")
    @cache(expire=60, namespace="fault-test")
    async def public() -> Dict[str, int]:
        calls["count"] += 1
        return {"count": calls["count"]}

    return app, calls


def test_backend_read_exception_recomputes_once_and_redacts_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    FastAPICache.init(ReadFailure(), prefix="fault-test")
    app, calls = _app()
    with caplog.at_level(logging.WARNING):
        with TestClient(app) as client:
            first = client.get("/public")
            second = client.get("/public")

    assert first.status_code == second.status_code == 200
    assert first.json() == {"count": 1}
    assert second.json() == {"count": 2}
    assert calls["count"] == 2
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "MISS"
    assert "ConnectionError" in caplog.text
    assert "synthetic-confidential-error-detail" not in caplog.text


def test_backend_write_exception_recomputes_on_next_request(
    caplog: pytest.LogCaptureFixture,
) -> None:
    FastAPICache.init(WriteFailure(), prefix="fault-test")
    app, calls = _app()
    with caplog.at_level(logging.WARNING):
        with TestClient(app) as client:
            first = client.get("/public")
            second = client.get("/public")

    assert [first.json(), second.json()] == [{"count": 1}, {"count": 2}]
    assert calls["count"] == 2
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "MISS"
    assert "TimeoutError" in caplog.text
    assert "synthetic-sensitive-write-detail" not in caplog.text
    # Current headers may contain ETag even if persistence failed. This test
    # characterizes the exception boundary, not an approved ETag policy.


def test_cancelled_backend_read_propagates_not_recomputed() -> None:
    FastAPICache.init(CancelledRead(), prefix="fault-test")
    calls = {"count": 0}

    @cache(expire=60)
    async def compute() -> int:
        calls["count"] += 1
        return calls["count"]

    async def verify() -> None:
        with pytest.raises(asyncio.CancelledError):
            await compute()

    asyncio.run(verify())
    assert calls["count"] == 0


def test_coder_encode_exception_is_not_silently_swallowed() -> None:
    FastAPICache.init(InMemoryBackend(), prefix="fault-test", coder=BrokenEncoder)

    @cache(expire=60)
    async def compute() -> int:
        return 42

    async def verify() -> None:
        with pytest.raises(ValueError, match="synthetic-coder-failure"):
            await compute()

    asyncio.run(verify())


@pytest.mark.redis
def test_caller_owned_redis_client_survives_pool_recycle() -> None:
    url = os.environ.get("REDIS_URL")
    if not url:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("Redis conformance requires a loopback REDIS_URL")
        pytest.skip("Redis integration requires REDIS_URL")
    if urlsplit(url).hostname not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail("Refusing Redis fault characterization outside loopback")
    try:
        from redis.asyncio import Redis

        from fastapi_cache.backends.redis import RedisBackend
    except ImportError:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("Redis extra required for the Redis integration profile")
        pytest.skip("Redis extra is not installed")

    async def verify() -> None:
        client = Redis.from_url(url, decode_responses=False)
        backend = RedisBackend(client)
        key = "fault-contract:" + uuid.uuid4().hex
        try:
            await backend.set(key, b"owned", expire=60)
            FastAPICache.init(backend, prefix="fault-contract")
            FastAPICache.reset()  # Does not own/close the supplied client.
            assert await backend.get(key) == b"owned"
            await client.connection_pool.disconnect()
            ttl, value = await backend.get_with_ttl(key)
            assert ttl > 0
            assert value == b"owned"
        finally:
            await backend.clear(key=key)
            closer = getattr(client, "aclose", None)
            if closer is None:
                closer = client.close
            await closer()

    asyncio.run(verify())

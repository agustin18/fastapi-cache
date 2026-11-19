"""Exploratory real-Redis compatibility checks for redis-py client releases.

These tests run in dedicated CI Redis containers. They do not establish
published support for redis-py majors outside the package metadata range.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

pytestmark = pytest.mark.redis


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        pytest.fail("REDIS_URL required for real Redis matrix tests")
    assert url is not None
    return url


async def _close_client(client: Any) -> None:
    aclose = getattr(client, "aclose", None)
    if aclose is not None:
        await aclose()
    else:
        await client.close()


def test_pipeline_ttl_binary_and_wrong_type() -> None:
    async def run() -> None:
        client = Redis.from_url(_redis_url(), decode_responses=False)
        try:
            await client.flushdb()
            backend = RedisBackend(client)
            key = "redis-client-matrix:binary"
            value = b"\x00\xff\x80test"
            await backend.set(key, value, expire=90)
            ttl, cached = await backend.get_with_ttl(key)
            assert isinstance(ttl, int)
            assert 0 < ttl <= 90
            assert cached == value
            assert await backend.get(key) == value

            await client.lpush("redis-client-matrix:wrong-type", "item")
            with pytest.raises(ResponseError):
                await backend.get("redis-client-matrix:wrong-type")

            await client.delete(key)
            missing_ttl, missing_value = await backend.get_with_ttl(key)
            assert missing_ttl == -2
            assert missing_value is None
        finally:
            await client.flushdb()
            await _close_client(client)

    asyncio.run(run())


def test_fastapi_miss_hit_uses_real_redis() -> None:
    calls = {"count": 0}

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        client = Redis.from_url(_redis_url(), decode_responses=False)
        try:
            await client.flushdb()
            FastAPICache.init(RedisBackend(client), prefix="redis-client-matrix")
            yield
        finally:
            FastAPICache.reset()
            await client.flushdb()
            await _close_client(client)

    app = FastAPI(lifespan=lifespan)

    @app.get("/cached")
    @cache(expire=90)
    async def cached(response: Response) -> Dict[str, int]:
        calls["count"] += 1
        return {"count": calls["count"]}

    with TestClient(app) as test_client:
        first = test_client.get("/cached")
        second = test_client.get("/cached")
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.headers.get("X-FastAPI-Cache") == "MISS"
        assert second.headers.get("X-FastAPI-Cache") == "HIT"
        assert first.json() == second.json() == {"count": 1}
        assert calls["count"] == 1

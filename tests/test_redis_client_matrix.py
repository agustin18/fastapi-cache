"""Real Redis compatibility probes; optional outside the dedicated matrix."""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

try:
    from redis.asyncio import Redis
    from redis.exceptions import AuthenticationError, ResponseError

    from fastapi_cache.backends.redis import RedisBackend
except ImportError:
    if os.environ.get("REQUIRE_REDIS") == "1":
        pytest.fail("Redis client is required by this matrix", pytrace=False)
    pytest.skip("optional redis client is not installed", allow_module_level=True)

pytestmark = pytest.mark.redis


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("REDIS_URL must be set for Redis matrix")
        pytest.skip("REDIS_URL is not configured")
    assert url is not None
    return url


async def _close(client: Any) -> None:
    aclose = getattr(client, "aclose", None)
    if aclose is not None:
        await aclose()
    else:
        await client.close()


def _client(*, decode: bool = False, protocol: Optional[int] = None) -> Any:
    kwargs: Dict[str, Any] = {"decode_responses": decode}
    if protocol is not None:
        kwargs["protocol"] = protocol
    return Redis.from_url(_redis_url(), **kwargs)


def _supports_explicit_resp() -> bool:
    from importlib.metadata import version

    return int(version("redis").split(".", 1)[0]) >= 5


@pytest.mark.parametrize("protocol", [None, 2, 3], ids=["default", "RESP2", "RESP3"])
def test_binary_ttl_pipeline_errors(protocol: Optional[int]) -> None:
    if protocol is not None and not _supports_explicit_resp():
        pytest.skip("Explicit protocol selection is only available in redis-py >= 5")

    async def run() -> None:
        client = _client(protocol=protocol)
        try:
            await client.flushdb()
            backend = RedisBackend(client)
            key = "matrix:binary"
            raw = b"\\x00\\xff\\x80payload"
            await backend.set(key, raw, expire=60)
            ttl, data = await backend.get_with_ttl(key)
            assert isinstance(ttl, int) and 0 < ttl <= 60
            assert data == raw
            assert await backend.get(key) == raw

            await client.set("matrix:permanent", "value")
            permanent_ttl, permanent_value = await backend.get_with_ttl("matrix:permanent")
            assert permanent_ttl == -1
            assert permanent_value == b"value"

            await client.lpush("matrix:wrong-type", "value")
            with pytest.raises(ResponseError):
                await backend.get("matrix:wrong-type")
            assert await client.ping()

            await client.delete(key)
            missing_ttl, missing = await backend.get_with_ttl(key)
            assert missing_ttl == -2 and missing is None

            await client.set("matrix:short-lived", "value", ex=1)
            await asyncio.sleep(1.2)
            assert await backend.get("matrix:short-lived") is None
        finally:
            await client.flushdb()
            await _close(client)

    asyncio.run(run())


@pytest.mark.parametrize("protocol", [None, 2, 3], ids=["default", "RESP2", "RESP3"])
def test_decoded_string_namespace_clear(protocol: Optional[int]) -> None:
    if protocol is not None and not _supports_explicit_resp():
        pytest.skip("Explicit protocol selection is only available in redis-py >= 5")

    async def run() -> None:
        client = _client(decode=True, protocol=protocol)
        try:
            await client.flushdb()
            backend = RedisBackend(client)
            await backend.set("matrix[tenant]:item:1", b"hello", expire=60)
            await backend.set("matrix[tenant]:item:2", b"world", expire=60)
            await backend.set("matrixxtenant:item:1", b"keep", expire=60)
            # Characterization: decode_responses=True returns a str, not bytes.
            # Cached JSON decoding is not part of the supported binary-client path.
            assert await backend.get("matrix[tenant]:item:1") == "hello"
            assert await backend.clear(namespace="matrix[tenant]:item") == 2
            assert await backend.get("matrix[tenant]:item:1") is None
            assert await backend.get("matrixxtenant:item:1") == "keep"
        finally:
            await client.flushdb()
            await _close(client)

    asyncio.run(run())


def test_authenticated_client_and_wrong_password() -> None:
    async def run() -> None:
        administrator = _client()
        username = "cache_matrix_probe"
        password = "test-only-password"
        try:
            await administrator.execute_command(
                "ACL", "SETUSER", username, "on", ">" + password, "~*", "+@all"
            )
            authorized = Redis.from_url(
                _redis_url(), username=username, password=password,
                decode_responses=False
            )
            denied = Redis.from_url(
                _redis_url(), username=username, password="invalid-password"
            )
            try:
                backend = RedisBackend(authorized)
                await backend.set("matrix:authenticated", b"ok", expire=60)
                assert await backend.get("matrix:authenticated") == b"ok"
                with pytest.raises(AuthenticationError):
                    await denied.ping()
            finally:
                await _close(authorized)
                await _close(denied)
        finally:
            await administrator.execute_command("ACL", "DELUSER", username)
            await administrator.delete("matrix:authenticated")
            await _close(administrator)

    asyncio.run(run())


def test_client_close_twice_is_idempotent() -> None:
    async def run() -> None:
        client = _client()
        assert await client.ping()
        await _close(client)
        await _close(client)

    asyncio.run(run())


def test_fastapi_miss_hit_real_redis() -> None:
    calls = {"count": 0}

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        client = _client()
        try:
            await client.flushdb()
            FastAPICache.init(RedisBackend(client), prefix="matrix")
            yield
        finally:
            FastAPICache.reset()
            await client.flushdb()
            await _close(client)

    app = FastAPI(lifespan=lifespan)

    @app.get("/cached")
    @cache(expire=60)
    async def endpoint(response: Response) -> Dict[str, int]:
        calls["count"] += 1
        return {"count": calls["count"]}

    with TestClient(app) as test_client:
        first = test_client.get("/cached")
        second = test_client.get("/cached")
        assert first.status_code == second.status_code == 200
        assert first.headers.get("X-FastAPI-Cache") == "MISS"
        assert second.headers.get("X-FastAPI-Cache") == "HIT"
        assert first.json() == second.json() == {"count": 1}
        assert calls["count"] == 1

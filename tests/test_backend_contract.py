"""Shared installed-interface conformance for supported local and Redis backends.

Redis uses only a randomly scoped key prefix on a local, test-only server.
It never flushes a database or connects to remote/production Redis.
"""
import asyncio
import os
import uuid
from typing import Any
from urllib.parse import urlsplit

import pytest

from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.types import Backend


@pytest.mark.parametrize(
    "kind",
    ["inmemory", pytest.param("redis", marks=pytest.mark.redis)],
)
def test_get_set_ttl_and_scoped_clear_contract(kind: str) -> None:
    async def verify() -> None:
        client: Any = None
        backend: Backend
        if kind == "redis":
            url = os.environ.get("REDIS_URL")
            if not url:
                if os.environ.get("REQUIRE_REDIS") == "1":
                    pytest.fail("Redis conformance requires REDIS_URL in Redis CI")
                pytest.skip("Redis integration requires REDIS_URL")
            if urlsplit(url).hostname not in ("localhost", "127.0.0.1", "::1"):
                pytest.fail("Refusing backend contract checks against non-loopback Redis")
            try:
                from redis.asyncio import Redis

                from fastapi_cache.backends.redis import RedisBackend
            except ImportError:
                if os.environ.get("REQUIRE_REDIS") == "1":
                    pytest.fail("Redis extra is required in Redis conformance CI")
                pytest.skip("Redis extra not installed")
            client = Redis.from_url(url, decode_responses=False)
            backend = RedisBackend(client)
        else:
            backend = InMemoryBackend()

        namespace = "contract-" + uuid.uuid4().hex
        public = namespace + ":alpha:item"
        sibling = namespace + ":alpha-extra:item"
        immortal = namespace + ":forever:item"
        missing = namespace + ":absent"
        empty_key = namespace + ":empty"
        immediate_key = namespace + ":zero-ttl"
        try:
            assert await backend.get(missing) is None
            missing_result = await backend.get_with_ttl(missing)
            assert isinstance(missing_result, tuple)
            missed_ttl, missed_value = missing_result
            # Redis reports -2 on missing; InMemory reports 0. Both are misses.
            assert missed_ttl <= 0
            assert missed_value is None

            await backend.set(immortal, b"persistent")
            assert await backend.get(immortal) == b"persistent"
            immortal_result = await backend.get_with_ttl(immortal)
            assert isinstance(immortal_result, tuple)
            assert immortal_result == (-1, b"persistent")

            # Empty bytes are a cache HIT, never conflated with a missing key.
            await backend.set(empty_key, b"", expire=60)
            assert await backend.get(empty_key) == b""
            empty_ttl, empty_value = await backend.get_with_ttl(empty_key)
            assert 0 < empty_ttl <= 60
            assert empty_value == b""
            assert await backend.clear(key=empty_key) == 1
            assert await backend.get(empty_key) is None

            # Same API, deliberately different provider semantics: Redis rejects
            # EX <= 0 while InMemory treats nonpositive TTL as immediate MISS.
            if kind == "inmemory":
                await backend.set(immediate_key, b"value", expire=0)
                assert await backend.get(immediate_key) is None
                assert await backend.get_with_ttl(immediate_key) == (0, None)
            else:
                from redis.exceptions import DataError, ResponseError

                with pytest.raises((DataError, ResponseError)):
                    await backend.set(immediate_key, b"value", expire=0)
                assert await backend.get(immediate_key) is None

            await backend.set(public, b"first", expire=60)
            await backend.set(sibling, b"untouched", expire=60)
            finite_result = await backend.get_with_ttl(public)
            assert isinstance(finite_result, tuple)
            remaining, value = finite_result
            assert 0 < remaining <= 60
            assert value == b"first"
            await backend.set(public, b"second", expire=60)
            assert await backend.get(public) == b"second"

            assert await backend.clear(namespace=namespace + ":alpha") == 1
            assert await backend.get(public) is None
            assert await backend.get(sibling) == b"untouched"
            assert await backend.clear(key=sibling) == 1
            assert await backend.clear(key=sibling) == 0
            assert await backend.get(sibling) is None
        finally:
            await backend.clear(namespace=namespace)
            if client is not None:
                close = getattr(client, "aclose", None)
                if close is None:
                    close = client.close
                await close()

    asyncio.run(verify())

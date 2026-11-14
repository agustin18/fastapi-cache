import asyncio
import os
from typing import Any, Generator, List

import pytest

from fastapi_cache import FastAPICache

try:
    from fastapi_cache.backends.redis import RedisBackend
except ImportError:
    RedisBackend = None  # type: ignore[misc, assignment]

pytestmark = pytest.mark.redis


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


@pytest.fixture
def redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("REDIS_URL must be set in the Redis integration job")
        pytest.skip("REDIS_URL is not set")
    assert url is not None
    return url


@pytest.fixture
def redis_backend_cls() -> Any:
    if RedisBackend is None:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("redis is not installed in the Redis integration job")
        pytest.skip("redis is not installed")
    return RedisBackend


def _client(url: str, decode_responses: bool = False) -> Any:
    from redis.asyncio import Redis

    if decode_responses:
        return Redis.from_url(url, decode_responses=True)
    return Redis.from_url(url, decode_responses=False)


def test_redis_key_only_clear_with_prefix(redis_url: str, redis_backend_cls: Any) -> None:
    async def run() -> None:
        client = _client(redis_url)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)
            FastAPICache.init(backend, prefix="app")
            await backend.set("app:user:one", b"one", expire=60)
            await backend.set("app:user:two", b"two", expire=60)

            assert await FastAPICache.clear(key="app:user:one") == 1
            assert await backend.get("app:user:one") is None
            assert await backend.get("app:user:two") == b"two"
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_namespace_boundary(redis_url: str, redis_backend_cls: Any) -> None:
    async def run() -> None:
        client = _client(redis_url)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)
            FastAPICache.init(backend, prefix="app")
            keys = [
                "app:user:one",
                "app:user:child:one",
                "app:users:one",
                "app:username:one",
                "app:user",
                "application:user:one",
            ]
            for key in keys:
                await backend.set(key, b"value", expire=60)

            assert await FastAPICache.clear(namespace="user") == 2
            assert await backend.get("app:user:one") is None
            assert await backend.get("app:user:child:one") is None
            for retained in (
                "app:users:one",
                "app:username:one",
                "app:user",
                "application:user:one",
            ):
                assert await backend.get(retained) == b"value"
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_no_arg_backend_clear_is_noop(redis_url: str, redis_backend_cls: Any) -> None:
    async def run() -> None:
        client = _client(redis_url)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)
            await backend.set("app:user:one", b"one", expire=60)

            assert await backend.clear() == 0
            assert await backend.get("app:user:one") == b"one"
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_nonexistent_key_returns_zero(redis_url: str, redis_backend_cls: Any) -> None:
    async def run() -> None:
        client = _client(redis_url)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)

            assert await backend.clear(key="app:missing") == 0
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_glob_literals(redis_url: str, redis_backend_cls: Any) -> None:
    async def run() -> None:
        client = _client(redis_url)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)
            FastAPICache.init(backend, prefix="app[*]")
            await backend.set("app[*]:one", b"one", expire=60)
            await backend.set("app[*]:two", b"two", expire=60)
            await backend.set("appX:one", b"other", expire=60)

            assert await FastAPICache.clear() == 2
            assert await backend.get("app[*]:one") is None
            assert await backend.get("app[*]:two") is None
            assert await backend.get("appX:one") == b"other"
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_count_is_unlink_result(redis_url: str, redis_backend_cls: Any) -> None:
    async def run() -> None:
        client = _client(redis_url)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)
            FastAPICache.init(backend, prefix="app")
            for index in range(3):
                await backend.set(f"app:user:{index}", b"value", expire=60)

            assert await FastAPICache.clear(namespace="user") == 3
            assert await FastAPICache.clear(namespace="user") == 0
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_decode_responses_true(redis_url: str, redis_backend_cls: Any) -> None:
    async def run() -> None:
        client = _client(redis_url, decode_responses=True)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)
            FastAPICache.init(backend, prefix="app")
            await backend.set("app:user:one", b"one", expire=60)
            await backend.set("app:user:two", b"two", expire=60)

            assert await FastAPICache.clear(namespace="user") == 2
            assert await backend.get("app:user:one") is None
            assert await backend.get("app:user:two") is None
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_namespace_clear_flushes_batches(
    redis_url: str, redis_backend_cls: Any
) -> None:
    async def run() -> None:
        client = _client(redis_url)
        try:
            await client.flushdb()
            backend = redis_backend_cls(client)
            backend._UNLINK_BATCH_SIZE = 2
            FastAPICache.init(backend, prefix="app")
            for index in range(3):
                await backend.set(f"app:user:{index}", b"value", expire=60)

            assert await FastAPICache.clear(namespace="user") == 3
        finally:
            await client.flushdb()
            await client.close()

    asyncio.run(run())


def test_redis_unlink_fallback_to_delete(redis_backend_cls: Any) -> None:
    class FakeRedis:
        def __init__(self) -> None:
            self.deleted: List[str] = []

        async def delete(self, *keys: str) -> int:
            self.deleted.extend(keys)
            return len(keys)

    fake = FakeRedis()
    backend = redis_backend_cls(fake)  # type: ignore[arg-type]

    assert asyncio.run(backend.clear(key="app:user:one")) == 1
    assert fake.deleted == ["app:user:one"]


def test_redis_namespace_clear_filters_non_matching_scan_keys(
    redis_backend_cls: Any,
) -> None:
    class FakeEncoder:
        def encode(self, value: str) -> bytes:
            return value.encode()

    class FakeRedis:
        def __init__(self) -> None:
            self.unlinked: List[bytes] = []

        def get_encoder(self) -> FakeEncoder:
            return FakeEncoder()

        async def scan_iter(self, match: str, count: int) -> Any:
            for key in (b"app:user:one", b"app:users:one"):
                yield key

        async def unlink(self, *keys: bytes) -> int:
            self.unlinked.extend(keys)
            return len(keys)

    fake = FakeRedis()
    backend = redis_backend_cls(fake)  # type: ignore[arg-type]

    assert asyncio.run(backend.clear(namespace="app:user")) == 1
    assert fake.unlinked == [b"app:user:one"]


def test_redis_cluster_namespace_clear_raises_without_scan(
    redis_backend_cls: Any,
) -> None:
    class FakeCluster:
        def __init__(self) -> None:
            self.scan_called = False

        def scan_iter(self, *args: Any, **kwargs: Any) -> Any:
            self.scan_called = True
            raise AssertionError("scan_iter must not be called")

    fake = FakeCluster()
    backend = redis_backend_cls(fake)  # type: ignore[arg-type]
    backend.is_cluster = True

    with pytest.raises(NotImplementedError):
        asyncio.run(backend.clear(namespace="app"))
    assert fake.scan_called is False


def test_redis_cluster_key_only_clear(redis_backend_cls: Any) -> None:
    class FakeCluster:
        def __init__(self) -> None:
            self.unlinked: List[str] = []

        async def unlink(self, *keys: str) -> int:
            self.unlinked.extend(keys)
            return len(keys)

    fake = FakeCluster()
    backend = redis_backend_cls(fake)  # type: ignore[arg-type]
    backend.is_cluster = True

    assert asyncio.run(backend.clear(key="app:user:one")) == 1
    assert fake.unlinked == ["app:user:one"]

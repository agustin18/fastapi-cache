"""D4 contracts on real supported stores and explicit experimental boundaries."""

import asyncio
import os
import uuid
from dataclasses import FrozenInstanceError
from typing import Any, List, Optional
from urllib.parse import urlsplit

import pytest

from fastapi_cache._backend_contract import Capability, backend_capabilities
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.types import Backend


def test_capabilities_are_exact_immutable_and_conservative() -> None:
    class Custom(InMemoryBackend):
        pass

    profile = backend_capabilities(InMemoryBackend())
    assert profile.read_write is Capability.SUPPORTED
    assert profile.remaining_ttl is Capability.SUPPORTED
    assert profile.clear_key is profile.clear_namespace is Capability.SUPPORTED
    assert profile.app_scope is Capability.SUPPORTED
    assert profile.compare_and_delete is Capability.UNSUPPORTED
    assert profile.ownership == "local"
    with pytest.raises(FrozenInstanceError):
        setattr(profile, "ownership", "owned")  # noqa: B010
    custom = backend_capabilities(Custom())
    assert custom.read_write is custom.remaining_ttl is Capability.UNKNOWN
    assert custom.clear_key is custom.clear_namespace is Capability.UNKNOWN
    assert custom.compare_and_delete is Capability.UNKNOWN
    assert custom.app_scope is Capability.UNSUPPORTED
    assert custom.ownership == "unknown"


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        if os.environ.get("REQUIRE_REDIS") == "1":
            pytest.fail("Redis D4 contract requires REDIS_URL")
        pytest.skip("Redis integration requires REDIS_URL")
    assert url is not None
    if urlsplit(url).hostname not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail("Refusing non-loopback Redis")
    return url


async def _close(client: Any) -> None:
    closer = getattr(client, "aclose", None)
    if closer is None:
        closer = client.close
    await closer()


@pytest.mark.parametrize(
    "kind", ["inmemory", "bounded", pytest.param("redis", marks=pytest.mark.redis)]
)
def test_overwrite_and_literal_clear_contract(kind: str) -> None:
    async def verify() -> None:
        client: Any = None
        backend: Backend
        if kind == "redis":
            url = _redis_url()
            from redis.asyncio import Redis

            from fastapi_cache.backends.redis import RedisBackend

            client = Redis.from_url(url, decode_responses=False)
            backend = RedisBackend(client)
        else:
            backend = InMemoryBackend(max_entries=32 if kind == "bounded" else None)
        root = "d4-" + uuid.uuid4().hex
        group = root + ":literal[*]?\\"
        target = group + ":one"
        sibling = group + "-other:one"
        bare = group
        other = root + ":unrelated"
        missing = root + ":missing"
        try:
            profile = backend_capabilities(backend)
            assert profile.read_write is profile.remaining_ttl is Capability.SUPPORTED
            assert profile.clear_namespace is profile.clear_key is Capability.SUPPORTED
            assert await backend.get_with_ttl(missing) == (-2 if client else 0, None)
            await backend.set(target, b"\x00\xff", expire=60)
            assert await backend.get(target) == b"\x00\xff"
            ttl, value = await backend.get_with_ttl(target)
            assert 0 < ttl <= 60 and value == b"\x00\xff"
            await backend.set(target, b"")
            assert await backend.get_with_ttl(target) == (-1, b"")
            await backend.set(target, b"new", expire=60)
            ttl, value = await backend.get_with_ttl(target)
            assert 0 < ttl <= 60 and value == b"new"
            for key in (sibling, bare, other):
                await backend.set(key, b"retain", expire=60)
            assert await backend.clear() == 0
            # Legacy ambiguity is intentionally preserved: nonempty namespace wins.
            assert await backend.clear(namespace=group, key=other) == 1
            assert await backend.clear(namespace=group) == 0
            for key in (sibling, bare, other):
                assert await backend.get(key) == b"retain"
            assert await backend.clear(namespace="", key=other) == 1
            assert await backend.clear(key=other) == 0
        finally:
            await backend.clear(namespace=root)
            if client is not None:
                await _close(client)

    asyncio.run(verify())


@pytest.mark.redis
def test_redis_capability_boundary_and_server_expiry() -> None:
    url = _redis_url()
    from redis.asyncio import Redis
    from redis.exceptions import DataError, ResponseError

    from fastapi_cache.backends.redis import RedisBackend

    async def verify() -> None:
        client = Redis.from_url(url, decode_responses=False)
        backend = RedisBackend(client)
        root = "d4-" + uuid.uuid4().hex
        key = root + ":value"
        try:
            assert backend_capabilities(backend).ownership == "borrowed"
            backend.is_cluster = True
            cluster = backend_capabilities(backend)
            assert cluster.read_write is cluster.remaining_ttl is Capability.EXPERIMENTAL
            assert cluster.clear_key is Capability.EXPERIMENTAL
            assert cluster.clear_namespace is cluster.app_scope is Capability.UNSUPPORTED
            with pytest.raises(NotImplementedError):
                await backend.clear(namespace=root)
            backend.is_cluster = False
            for expire in (0, -1):
                with pytest.raises((DataError, ResponseError)):
                    await backend.set(key, b"bad", expire=expire)
                assert await backend.get(key) is None
            await backend.set(key, b"live", expire=60)
            assert 0 < await client.pttl(key) <= 60000
            # Redis reports seconds rounded; zero is not by itself a miss.
            # Use PEXPIRE for a subsecond envelope and assert conditional on
            # observed payload, then force an elapsed deadline server-side.
            assert await client.pexpire(key, 400)
            ttl, value = await backend.get_with_ttl(key)
            if value is not None:
                assert ttl == 0 and value == b"live"
            else:
                assert ttl == -2
            await client.pexpire(key, 0)
            assert await backend.get(key) is None
            assert await backend.get_with_ttl(key) == (-2, None)
        finally:
            backend.is_cluster = False
            await backend.clear(namespace=root)
            await _close(client)

    asyncio.run(verify())


@pytest.mark.parametrize("capacity", [None, 4])
def test_inmemory_cancel_waiting_for_lock_has_no_effect(capacity: Optional[int]) -> None:
    async def verify() -> None:
        backend = InMemoryBackend(max_entries=capacity)
        await backend.set("d4:existing", b"old")
        entered = asyncio.Event()

        async def blocked() -> None:
            entered.set()
            await backend.set("d4:existing", b"new")

        async with backend._get_lock():
            task = asyncio.create_task(blocked())
            await asyncio.wait_for(entered.wait(), 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert await backend.get("d4:existing") == b"old"
        assert await backend.clear(namespace="d4") == 1

    asyncio.run(verify())


@pytest.mark.redis
@pytest.mark.parametrize("failure", ["cancel", "error"])
def test_redis_partial_clear_and_unknown_write_outcome(
    failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = _redis_url()
    from redis.asyncio import Redis

    from fastapi_cache.backends.redis import RedisBackend

    async def verify() -> None:
        client = Redis.from_url(url, decode_responses=False)
        backend = RedisBackend(client)
        root = "d4-" + uuid.uuid4().hex
        keys = [root + ":group:one", root + ":group:two"]
        sibling = root + ":groups:one"
        entered = asyncio.Event()
        removed: List[Any] = []
        unlink = client.unlink
        set_value = client.set

        async def partial(*args: Any) -> int:
            if removed:
                entered.set()
                if failure == "error":
                    raise ConnectionError("synthetic partial clear")
                await asyncio.Event().wait()
            count = await unlink(*args)
            removed.extend(args)
            return count

        calls = []

        async def ambiguous(*args: Any, **kwargs: Any) -> Any:
            calls.append(1)
            await set_value(*args, **kwargs)
            raise TimeoutError("synthetic uncertain write")

        try:
            for key in [*keys, sibling]:
                await backend.set(key, b"value", expire=60)
            with monkeypatch.context() as patch:
                patch.setattr(backend, "_UNLINK_BATCH_SIZE", 1)
                patch.setattr(client, "unlink", partial)
                task = asyncio.create_task(backend.clear(namespace=root + ":group"))
                await asyncio.wait_for(entered.wait(), 5)
                if failure == "cancel":
                    task.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await task
                else:
                    with pytest.raises(ConnectionError, match="synthetic partial clear"):
                        await task
            assert len(removed) == 1
            survivors = [await backend.get(key) for key in keys]
            assert survivors.count(None) == survivors.count(b"value") == 1
            assert await backend.get(sibling) == b"value"
            with monkeypatch.context() as patch:
                patch.setattr(client, "set", ambiguous)
                with pytest.raises(TimeoutError, match="synthetic uncertain write"):
                    await backend.set(sibling, b"committed", expire=60)
            assert calls == [1]
            assert await backend.get(sibling) == b"committed"
        finally:
            await backend.clear(namespace=root)
            await _close(client)

    asyncio.run(verify())

"""Characterization of installed experimental adapters; not service parity."""

import asyncio
from typing import Any

import pytest

from fastapi_cache._backend_contract import Capability, backend_capabilities


def test_memcached_fixed_ttl_and_unsupported_clear() -> None:
    pytest.importorskip("aiomcache")
    from fastapi_cache.backends.memcached import MemcachedBackend

    class Client:
        async def get(self, key: bytes) -> Any:
            return b"" if key == b"present" else None

    async def verify() -> None:
        backend = MemcachedBackend(Client())  # type: ignore[arg-type]
        profile = backend_capabilities(backend)
        assert profile.read_write is Capability.EXPERIMENTAL
        assert profile.remaining_ttl is Capability.UNSUPPORTED
        assert profile.clear_key is profile.clear_namespace is Capability.UNSUPPORTED
        assert profile.app_scope is Capability.UNSUPPORTED
        assert profile.ownership == "borrowed"
        assert await backend.get_with_ttl("present") == (3600, b"")
        assert await backend.get_with_ttl("absent") == (3600, None)
        with pytest.raises(NotImplementedError):
            await backend.clear(key="present")
        with pytest.raises(NotImplementedError):
            await backend.clear(namespace="group")

    asyncio.run(verify())


def test_dynamodb_expired_read_and_close_gap() -> None:
    pytest.importorskip("aiobotocore")
    from fastapi_cache.backends.dynamodb import DynamoBackend

    class Client:
        async def get_item(self, **kwargs: Any) -> Any:
            return {"Item": {"value": {"B": b"expired"}, "ttl": {"N": "1"}}}

        async def __aexit__(self, *args: Any) -> None:
            return None

    async def verify() -> None:
        backend = DynamoBackend("synthetic")
        backend.client = Client()  # type: ignore[assignment]
        profile = backend_capabilities(backend)
        assert profile.read_write is profile.remaining_ttl is Capability.EXPERIMENTAL
        assert profile.clear_key is profile.clear_namespace is Capability.UNSUPPORTED
        assert profile.app_scope is Capability.UNSUPPORTED
        assert profile.ownership == "experimental"
        # Explicitly reproduce #45, do not mark this as supported behavior.
        assert await backend.get("expired") == b"expired"
        assert await backend.get_with_ttl("expired") == (0, None)
        with pytest.raises(NotImplementedError):
            await backend.clear(key="expired")
        await backend.close()
        assert backend.client is None
        with pytest.raises(AttributeError):
            await backend.close()

    asyncio.run(verify())

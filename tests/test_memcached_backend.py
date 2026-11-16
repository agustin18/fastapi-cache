import asyncio
from typing import Any, Dict, List, Optional, Tuple

import pytest

try:
    from fastapi_cache.backends.memcached import MemcachedBackend
except ImportError:
    MemcachedBackend = None


class FakeMemcachedClient:
    """Minimal aiomcache-compatible client that records calls."""

    def __init__(self) -> None:
        self.store: Dict[bytes, bytes] = {}
        self.calls: List[Tuple[str, Any]] = []

    async def get(self, key: bytes) -> Optional[bytes]:
        self.calls.append(("get", key))
        return self.store.get(key)

    async def set(self, key: bytes, value: bytes, exptime: int = 0) -> bool:
        self.calls.append(("set", (key, value, exptime)))
        self.store[key] = value
        return True


@pytest.fixture
def memcached_backend_cls() -> Any:
    if MemcachedBackend is None:
        pytest.skip("aiomcache is not installed")
    return MemcachedBackend


@pytest.fixture
def client() -> FakeMemcachedClient:
    return FakeMemcachedClient()


@pytest.fixture
def backend(client: FakeMemcachedClient, memcached_backend_cls: Any) -> Any:
    return memcached_backend_cls(client)


def test_key_is_encoded_to_bytes(
    backend: MemcachedBackend, client: FakeMemcachedClient
) -> None:
    asyncio.run(backend.set("app:key", b"value", expire=30))

    assert client.calls == [("set", (b"app:key", b"value", 30))]


def test_get_returns_stored_value(backend: MemcachedBackend) -> None:
    async def run() -> Optional[bytes]:
        await backend.set("app:key", b"value", expire=30)
        return await backend.get("app:key")

    assert asyncio.run(run()) == b"value"


def test_get_miss_returns_none(backend: MemcachedBackend) -> None:
    assert asyncio.run(backend.get("app:missing")) is None


def test_set_without_expire_sends_zero(
    backend: MemcachedBackend, client: FakeMemcachedClient
) -> None:
    asyncio.run(backend.set("app:key", b"value"))

    assert client.calls[-1] == ("set", (b"app:key", b"value", 0))


def test_get_with_ttl_reports_fixed_3600(backend: MemcachedBackend) -> None:
    """Documented limitation: the TTL is hardcoded, not the real remaining time."""

    async def run() -> Tuple[int, Optional[bytes]]:
        await backend.set("app:key", b"value", expire=5)
        return await backend.get_with_ttl("app:key")

    ttl, value = asyncio.run(run())

    assert ttl == 3600
    assert value == b"value"


def test_get_with_ttl_miss_returns_fixed_3600_and_none(
    backend: MemcachedBackend,
) -> None:
    ttl, value = asyncio.run(backend.get_with_ttl("app:missing"))

    assert ttl == 3600
    assert value is None


def test_clear_is_not_implemented(backend: MemcachedBackend) -> None:
    with pytest.raises(NotImplementedError):
        asyncio.run(backend.clear())

    with pytest.raises(NotImplementedError):
        asyncio.run(backend.clear(namespace="app"))

    with pytest.raises(NotImplementedError):
        asyncio.run(backend.clear(key="app:key"))

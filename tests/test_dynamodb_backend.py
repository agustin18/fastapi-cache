import asyncio
import datetime
from typing import Any, Dict, List, Optional, Tuple

import pytest

try:
    from fastapi_cache.backends.dynamodb import DynamoBackend
except ImportError:
    DynamoBackend = None


class FakeDynamoClient:
    """Minimal aiobotocore DynamoDB client that records calls."""

    def __init__(self) -> None:
        self.items: Dict[str, Dict[str, Any]] = {}
        self.calls: List[Tuple[str, str, Dict[str, Any]]] = []

    async def get_item(
        self, *, TableName: str, Key: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.calls.append(("get_item", TableName, Key))
        item = self.items.get(Key["key"]["S"])
        if item is None:
            return {}
        return {"Item": item}

    async def put_item(
        self, *, TableName: str, Item: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.calls.append(("put_item", TableName, Item))
        self.items[Item["key"]["S"]] = Item
        return {}


@pytest.fixture
def dynamodb_backend_cls() -> Any:
    if DynamoBackend is None:
        pytest.skip("aiobotocore is not installed")
    return DynamoBackend


@pytest.fixture
def client() -> FakeDynamoClient:
    return FakeDynamoClient()


@pytest.fixture
def backend(client: FakeDynamoClient, dynamodb_backend_cls: Any) -> Any:
    instance = dynamodb_backend_cls(table_name="cache", region="eu-west-1")
    instance.client = client
    return instance


def test_get_miss_returns_none(backend: DynamoBackend) -> None:
    assert asyncio.run(backend.get("app:missing")) is None


def test_set_writes_key_and_value_attributes(
    backend: DynamoBackend, client: FakeDynamoClient
) -> None:
    asyncio.run(backend.set("app:key", b"value"))

    _, table_name, item = client.calls[-1]
    assert table_name == "cache"
    assert item["key"] == {"S": "app:key"}
    assert item["value"] == {"B": b"value"}
    assert "ttl" not in item


def test_set_with_expire_writes_ttl_attribute(
    backend: DynamoBackend, client: FakeDynamoClient
) -> None:
    before = int(datetime.datetime.now().timestamp())
    asyncio.run(backend.set("app:key", b"value", expire=60))
    after = int(datetime.datetime.now().timestamp())

    _, _, item = client.calls[-1]
    ttl = int(item["ttl"]["N"])
    assert before + 60 <= ttl <= after + 60


def test_get_returns_stored_value(backend: DynamoBackend) -> None:
    async def run() -> Optional[bytes]:
        await backend.set("app:key", b"value", expire=60)
        return await backend.get("app:key")

    assert asyncio.run(run()) == b"value"


def test_get_with_ttl_returns_remaining_seconds(backend: DynamoBackend) -> None:
    async def run() -> Tuple[int, Optional[bytes]]:
        await backend.set("app:key", b"value", expire=60)
        return await backend.get_with_ttl("app:key")

    ttl, value = asyncio.run(run())

    assert 55 <= ttl <= 60
    assert value == b"value"


def test_get_with_ttl_returns_minus_one_without_expire(
    backend: DynamoBackend,
) -> None:
    async def run() -> Tuple[int, Optional[bytes]]:
        await backend.set("app:key", b"value")
        return await backend.get_with_ttl("app:key")

    ttl, value = asyncio.run(run())

    assert ttl == -1
    assert value == b"value"


def test_get_with_ttl_treats_expired_entry_as_miss(
    backend: DynamoBackend, client: FakeDynamoClient
) -> None:
    client.items["app:key"] = {
        "key": {"S": "app:key"},
        "value": {"B": b"value"},
        "ttl": {"N": "1"},
    }

    ttl, value = asyncio.run(backend.get_with_ttl("app:key"))

    assert ttl == 0
    assert value is None


def test_get_with_ttl_miss_returns_zero_and_none(
    backend: DynamoBackend,
) -> None:
    ttl, value = asyncio.run(backend.get_with_ttl("app:missing"))

    assert ttl == 0
    assert value is None


def test_clear_is_not_implemented(backend: DynamoBackend) -> None:
    with pytest.raises(NotImplementedError):
        asyncio.run(backend.clear())

    with pytest.raises(NotImplementedError):
        asyncio.run(backend.clear(namespace="app"))

    with pytest.raises(NotImplementedError):
        asyncio.run(backend.clear(key="app:key"))

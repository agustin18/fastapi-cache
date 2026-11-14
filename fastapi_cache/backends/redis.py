from typing import List, Optional, Tuple, Union

from redis.asyncio.client import Redis
from redis.asyncio.cluster import RedisCluster

from fastapi_cache.types import Backend

_GLOB_METACHARACTERS = frozenset("*?[]\\")


def _escape_glob(value: str) -> str:
    return "".join(
        "\\" + character if character in _GLOB_METACHARACTERS else character
        for character in value
    )


def _matches_namespace(
    cache_key: Union[bytes, str], boundary: str, boundary_bytes: bytes
) -> bool:
    if isinstance(cache_key, bytes):
        return cache_key.startswith(boundary_bytes)
    return cache_key.startswith(boundary)


class RedisBackend(Backend):
    _SCAN_COUNT = 1000
    _UNLINK_BATCH_SIZE = 500

    def __init__(self, redis: Union["Redis[bytes]", "RedisCluster[bytes]"]):
        self.redis = redis
        self.is_cluster: bool = isinstance(redis, RedisCluster)

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        async with self.redis.pipeline(transaction=not self.is_cluster) as pipe:
            return await pipe.ttl(key).get(key).execute()  # type: ignore[union-attr,no-any-return]

    async def get(self, key: str) -> Optional[bytes]:
        return await self.redis.get(key)  # type: ignore[union-attr]

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        await self.redis.set(key, value, ex=expire)  # type: ignore[union-attr]

    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        if namespace:
            if self.is_cluster:
                raise NotImplementedError(
                    "Redis Cluster namespace clearing is not supported; "
                    "use clear(key=...) or flush the database out of band"
                )
            return await self._clear_namespace(namespace)
        if key:
            return await self._unlink([key])
        return 0

    async def _clear_namespace(self, namespace: str) -> int:
        encoder = self.redis.get_encoder()  # type: ignore[union-attr]
        boundary = namespace + ":"
        boundary_bytes = bytes(encoder.encode(boundary))
        pattern = f"{_escape_glob(namespace)}:*"
        count = 0
        batch: List[Union[bytes, str]] = []
        async for cache_key in self.redis.scan_iter(  # type: ignore[union-attr]
            match=pattern, count=self._SCAN_COUNT
        ):
            if not _matches_namespace(cache_key, boundary, boundary_bytes):
                continue
            batch.append(cache_key)
            if len(batch) >= self._UNLINK_BATCH_SIZE:
                count += await self._unlink(batch)
                batch.clear()
        if batch:
            count += await self._unlink(batch)
        return count

    async def _unlink(self, keys: List[Union[bytes, str]]) -> int:
        unlink = getattr(self.redis, "unlink", None)
        if unlink is None:
            return await self.redis.delete(*keys)  # type: ignore[union-attr]
        return await unlink(*keys)  # type: ignore[no-any-return]

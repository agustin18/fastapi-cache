import time
from asyncio import Lock
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi_cache.types import Backend


@dataclass
class Value:
    data: bytes
    ttl_ts: Optional[int]


class InMemoryBackend(Backend):
    def __init__(self) -> None:
        self._store: Dict[str, Value] = {}
        self._lock: Optional[Lock] = None

    def _get_lock(self) -> Lock:
        if self._lock is None:
            self._lock = Lock()
        return self._lock

    @property
    def _now(self) -> int:
        return int(time.time())

    def _get(self, key: str) -> Optional[Value]:
        v = self._store.get(key)
        if v:
            if v.ttl_ts is not None and v.ttl_ts < self._now:
                del self._store[key]
            else:
                return v
        return None

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        async with self._get_lock():
            v = self._get(key)
            if v:
                if v.ttl_ts is None:
                    return -1, v.data
                return v.ttl_ts - self._now, v.data
            return 0, None

    async def get(self, key: str) -> Optional[bytes]:
        async with self._get_lock():
            v = self._get(key)
            if v:
                return v.data
            return None

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        async with self._get_lock():
            ttl_ts = None if expire is None else self._now + expire
            self._store[key] = Value(value, ttl_ts)

    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        count = 0
        async with self._get_lock():
            if namespace:
                boundary = namespace + ":"
                keys = list(self._store.keys())
                for cache_key in keys:
                    if cache_key.startswith(boundary):
                        del self._store[cache_key]
                        count += 1
            elif key:
                if key in self._store:
                    del self._store[key]
                    count += 1
        return count

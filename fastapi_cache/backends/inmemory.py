"""In-process cache with optional bounded, per-instance LRU capacity.

Unbounded default preserves lazy expiration; exact TTL boundaries expire
when the integer-second deadline is reached (no zero-TTL stale reads).
Bounded writes use an indexed min-heap for expiry and an OrderedDict
for recency: O(log capacity), no full-store scans on ordinary writes.
"""

import time
from asyncio import Lock
from dataclasses import dataclass
from typing import Dict, List, Optional, OrderedDict, Tuple

from fastapi_cache.types import Backend


@dataclass
class Value:
    data: bytes
    ttl_ts: Optional[int]


class _ExpirationIndex:
    """Exact (no stale entries) indexed min-heap of (expiry, key).

    Unlike a lazy heap with generation tombstones, this needs at most
    one heap entry per live cache key; overwrites and evictions remove
    the old expiry in O(log n), without periodic O(n) heap compaction.
    """

    def __init__(self) -> None:
        self._heap: List[Tuple[int, str]] = []
        self._positions: Dict[str, int] = {}

    def __len__(self) -> int:
        return len(self._heap)

    def _swap(self, left: int, right: int) -> None:
        items = self._heap
        items[left], items[right] = items[right], items[left]
        self._positions[items[left][1]] = left
        self._positions[items[right][1]] = right

    def _sift_up(self, index: int) -> None:
        while index:
            parent = (index - 1) // 2
            if self._heap[parent] <= self._heap[index]:
                return
            self._swap(parent, index)
            index = parent

    def _sift_down(self, index: int) -> None:
        length = len(self._heap)
        while True:
            left = index * 2 + 1
            if left >= length:
                return
            right = left + 1
            smallest = left
            if right < length and self._heap[right] < self._heap[left]:
                smallest = right
            if self._heap[index] <= self._heap[smallest]:
                return
            self._swap(index, smallest)
            index = smallest

    def discard(self, key: str) -> None:
        index = self._positions.pop(key, None)
        if index is None:
            return
        last = self._heap.pop()
        if index == len(self._heap):
            return
        self._heap[index] = last
        self._positions[last[1]] = index
        if index and self._heap[index] < self._heap[(index - 1) // 2]:
            self._sift_up(index)
        else:
            self._sift_down(index)

    def update(self, key: str, expires_at: Optional[int]) -> None:
        self.discard(key)
        if expires_at is None:
            return
        index = len(self._heap)
        self._heap.append((expires_at, key))
        self._positions[key] = index
        self._sift_up(index)

    def oldest_expired(self, now: int) -> Optional[str]:
        if self._heap and self._heap[0][0] <= now:
            return self._heap[0][1]
        return None


class InMemoryBackend(Backend):
    def __init__(self, *, max_entries: Optional[int] = None) -> None:
        if max_entries is not None and (
            isinstance(max_entries, bool)
            or not isinstance(max_entries, int)
            or max_entries < 1
        ):
            raise ValueError("max_entries must be a positive integer or None")
        # Capacity is fixed at construction: runtime resizing would require
        # coordinated eviction and index rebuilding under the async lock.
        self._max_entries = max_entries
        self._store: Dict[str, Value] = {}
        self._recency: Optional[OrderedDict[str, None]] = (
            OrderedDict() if max_entries is not None else None
        )
        self._expiry_index: Optional[_ExpirationIndex] = (
            _ExpirationIndex() if max_entries is not None else None
        )
        self._lock: Optional[Lock] = None

    @property
    def max_entries(self) -> Optional[int]:
        """Immutable per-instance entry cap, or None for legacy unbounded mode."""
        return self._max_entries

    def _get_lock(self) -> Lock:
        if self._lock is None:
            self._lock = Lock()
        return self._lock

    @property
    def _now(self) -> int:
        return int(time.time())

    def _discard(self, key: str) -> None:
        self._store.pop(key, None)
        if self._recency is not None:
            self._recency.pop(key, None)
        if self._expiry_index is not None:
            self._expiry_index.discard(key)

    def _get(self, key: str) -> Optional[Value]:
        v = self._store.get(key)
        if v:
            if v.ttl_ts is not None and v.ttl_ts <= self._now:
                self._discard(key)
            else:
                if self._recency is not None:
                    self._recency.move_to_end(key)
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
            if self._recency is not None and self.max_entries is not None:
                # Each new key needs at most ONE freed slot. Reclaim the
                # earliest expired entry first, not an arbitrary live LRU
                # entry. No scan and no unbounded cleanup under the lock.
                if key not in self._store and len(self._store) >= self.max_entries:
                    assert self._expiry_index is not None  # noqa: S101
                    expired = self._expiry_index.oldest_expired(self._now)
                    if expired is not None:
                        self._discard(expired)
                    else:
                        self._discard(next(iter(self._recency)))
            self._store[key] = Value(value, ttl_ts)
            if self._recency is not None:
                self._recency[key] = None
                self._recency.move_to_end(key)
            if self._expiry_index is not None:
                self._expiry_index.update(key, ttl_ts)

    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        count = 0
        async with self._get_lock():
            if namespace:
                boundary = namespace + ":"
                keys = list(self._store.keys())
                for cache_key in keys:
                    if cache_key.startswith(boundary):
                        self._discard(cache_key)
                        count += 1
            elif key:
                if key in self._store:
                    self._discard(key)
                    count += 1
        return count

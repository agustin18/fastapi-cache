"""Seeded state-machine regression for the indexed TTL heap and LRU (#54)."""

import asyncio
import random
from collections import OrderedDict
from typing import Dict, Optional, Tuple
from typing import OrderedDict as OrderedDictType

import pytest

from fastapi_cache.backends.inmemory import InMemoryBackend

Entry = Tuple[bytes, Optional[int]]


@pytest.mark.parametrize("seed", range(20))
def test_seeded_bounded_inmemory_fuzz(
    seed: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """20 deterministic seeds × 2,000 reads/writes/TTL/clears, no Hypothesis dep."""
    now = [1000]
    monkeypatch.setattr("fastapi_cache.backends.inmemory.time.time", lambda: now[0])
    rng = random.Random(seed)  # noqa: S311 - deterministic test data, not security
    capacity = 1 + seed % 17
    reference: OrderedDictType[str, Entry] = OrderedDict()

    def reference_get(key: str) -> Optional[Entry]:
        val = reference.get(key)
        if val is not None:
            if val[1] is not None and val[1] <= now[0]:
                del reference[key]
                return None
            reference.move_to_end(key)
        return val

    def reference_set(key: str, value: bytes, expire: Optional[int]) -> None:
        if key not in reference and len(reference) >= capacity:
            candidates = sorted(
                (ttl, k)
                for k, (_, ttl) in reference.items()
                if ttl is not None and ttl <= now[0]
            )
            if candidates:
                del reference[candidates[0][1]]
            else:
                reference.popitem(last=False)
        reference[key] = (value, None if expire is None else now[0] + expire)
        reference.move_to_end(key)

    def reference_clear(namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        if namespace:
            keys = [k for k in reference if k.startswith(namespace + ":")]
            for k in keys:
                del reference[k]
            return len(keys)
        if key and key in reference:
            del reference[key]
            return 1
        return 0

    def assert_invariants(backend: InMemoryBackend) -> None:
        store = backend._store  # pyright: ignore[reportPrivateUsage]
        recency = backend._recency  # pyright: ignore[reportPrivateUsage]
        index = backend._expiry_index  # pyright: ignore[reportPrivateUsage]
        assert recency is not None
        assert index is not None
        assert len(store) <= capacity
        assert list(recency) == list(reference)
        assert set(store) == set(reference)
        for key, val in reference.items():
            assert store[key].data == val[0]
            assert store[key].ttl_ts == val[1]
        heap = index._heap  # pyright: ignore[reportPrivateUsage]
        positions: Dict[str, int] = index._positions  # pyright: ignore[reportPrivateUsage]
        expected_expiry = {
            k: ttl for k, (_, ttl) in reference.items() if ttl is not None
        }
        assert len(heap) == len(positions) == len(expected_expiry)
        assert set(positions) == set(expected_expiry)
        for position, (ttl, key) in enumerate(heap):
            assert positions[key] == position
            assert ttl == expected_expiry[key]
            if position:
                assert heap[(position - 1) // 2] <= heap[position]

    async def run() -> None:
        backend = InMemoryBackend(max_entries=capacity)
        names = [
            f"{namespace}:{index}" for namespace in ("a", "ab", "b")
            for index in range(30)
        ]
        for i in range(2000):
            action = rng.randrange(100)
            key = rng.choice(names)
            if action < 48:
                ttl = rng.choice([None, 0, 1, 2, 5, 12, 100])
                value = f"{seed}:{i}".encode()
                reference_set(key, value, ttl)
                await backend.set(key, value, expire=ttl)
            elif action < 68:
                item = reference_get(key)
                assert await backend.get(key) == (None if item is None else item[0])
            elif action < 82:
                item = reference_get(key)
                expected_ttl = (
                    (0, None)
                    if item is None
                    else ((-1, item[0]) if item[1] is None else (item[1] - now[0], item[0]))
                )
                assert await backend.get_with_ttl(key) == expected_ttl
            elif action < 90:
                expected_n = reference_clear(key=key)
                assert await backend.clear(key=key) == expected_n
            elif action < 96:
                namespace = rng.choice(["a", "ab", "b"])
                expected_n = reference_clear(namespace=namespace)
                assert await backend.clear(namespace=namespace) == expected_n
            else:
                now[0] += rng.randrange(1, 7)
            assert_invariants(backend)

    asyncio.run(run())

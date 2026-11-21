"""Bounded InMemory scaling gate: fill, full-capacity LRU and TTL reclaim.

Run on both legacy Python 3.8 and supported modern Python. This test
benchmarks pure backend operations (not real request latency).
"""

import argparse
import asyncio
import json
import sys
import time
from typing import Dict, Tuple

from fastapi_cache.backends.inmemory import InMemoryBackend


class _FixedClockBackend(InMemoryBackend):
    """Deterministic TTL benchmark: no real-time sleep or machine clock drift."""

    def __init__(self, capacity: int) -> None:
        super().__init__(max_entries=capacity)
        self.now = 1000

    @property
    def _now(self) -> int:
        return self.now


async def measure(capacity: int) -> Tuple[Dict[str, float], Dict[str, int]]:
    value = b"small-payload"
    backend = _FixedClockBackend(capacity)
    start = time.perf_counter()
    for i in range(capacity):
        await backend.set("initial:" + str(i), value, expire=600)
    fill = time.perf_counter() - start

    # Run a complete second capacity worth of NEW keys after the cache
    # fills: every write MUST evict the least-recently-used live key.
    start = time.perf_counter()
    for i in range(capacity):
        await backend.set("churn:" + str(i), value, expire=600)
    churn = time.perf_counter() - start
    if len(backend._store) != capacity:  # pyright: ignore[reportPrivateUsage]
        raise AssertionError("capacity violated during full LRU churn")

    expired_backend = _FixedClockBackend(capacity)
    for i in range(capacity):
        await expired_backend.set("stale:" + str(i), value, expire=1)
    expired_backend.now = 1002  # All old entries have expired.
    start = time.perf_counter()
    for i in range(capacity):
        await expired_backend.set("reclaimed:" + str(i), value, expire=600)
    expiry_reclaim = time.perf_counter() - start
    if len(expired_backend._store) != capacity:  # pyright: ignore[reportPrivateUsage]
        raise AssertionError("capacity violated during TTL reclaim")
    if await expired_backend.get("stale:0") is not None:
        raise AssertionError("expired keys were not reclaimed")

    return (
        {"fill": fill, "full_lru_churn": churn, "full_expiry_reclaim": expiry_reclaim},
        {"fill": capacity, "full_lru_churn": capacity, "full_expiry_reclaim": capacity},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assert-scaling", action="store_true")
    args = parser.parse_args()

    asyncio.run(measure(300))  # Warm up imports/loop and code paths.
    results = {}
    for capacity in (10_000, 100_000):
        durations, counts = asyncio.run(measure(capacity))
        results[capacity] = {
            "seconds": durations,
            "ms_per_write": {
                key: durations[key] * 1000 / counts[key] for key in durations
            },
        }
    growth = {
        key: results[100_000]["ms_per_write"][key] /
        results[10_000]["ms_per_write"][key]
        for key in ("fill", "full_lru_churn", "full_expiry_reclaim")
    }
    print(json.dumps({
        "python": sys.version.split()[0],
        "capacity": [10_000, 100_000],
        "measurements": results,
        "per_write_growth_100k_vs_10k": growth,
        "note": "CI microbenchmark, not endpoint latency or payload-byte bound",
    }, indent=2))
    if args.assert_scaling:
        for operation, ratio in growth.items():
            if ratio > 4.5:
                raise AssertionError(
                    f"{operation} grew {ratio:.2f}x per write from 10k to 100k; "
                    "an O(N) scan or regression is likely."
                )


if __name__ == "__main__":
    main()

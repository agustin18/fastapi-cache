"""Repeatable bounded InMemory 10k/100k write benchmark.

This deliberately asserts algorithmic scaling rather than an absolute
runtime threshold that would be brittle on shared CI hardware.
"""

import argparse
import asyncio
import json
import time

from fastapi_cache.backends.inmemory import InMemoryBackend


async def measure_writes(count: int) -> float:
    backend = InMemoryBackend(max_entries=count)
    started = time.perf_counter()
    for index in range(count):
        await backend.set("benchmark:" + str(index), b"small-payload", expire=600)
    elapsed = time.perf_counter() - started
    if len(backend._store) != count:  # pyright: ignore[reportPrivateUsage]
        raise AssertionError("bounded writes did not retain the target size")
    return elapsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assert-scaling", action="store_true")
    args = parser.parse_args()
    # Warm up imports and event loop. Always run both scales, even in CI.
    asyncio.run(measure_writes(300))
    results = {
        size: asyncio.run(measure_writes(size))
        for size in (10_000, 100_000)
    }
    per_write_ms = {
        size: elapsed * 1000 / size
        for size, elapsed in results.items()
    }
    growth = per_write_ms[100_000] / per_write_ms[10_000]
    print(
        json.dumps(
            {
                "python": __import__("sys").version.split()[0],
                "seconds": results,
                "milliseconds_per_write": per_write_ms,
                "cost_growth_100k_vs_10k": growth,
                "note": "single-worker microbenchmark; no payload-byte bound",
            },
            indent=2,
        )
    )
    if args.assert_scaling and growth > 4.0:
        raise AssertionError(
            f"Per-write cost grew {growth:.2f}x from 10k to 100k; "
            "expected near O(log N), not O(N) full-store scans."
        )


if __name__ == "__main__":
    main()

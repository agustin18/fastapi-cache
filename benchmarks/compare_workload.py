"""Identical public-interface workload for published 0.5.0 and 0.6.0 wheels.

No bounded 0.6.0 InMemory, authentication, events or release-candidate APIs.
HTTP uses in-process ASGITransport; Redis uses real loopback standalone 7.4.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import importlib.metadata as metadata
import json
import math
import platform
import statistics
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI
from redis.asyncio import Redis

import fastapi_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


class Recorder:
    def __init__(self) -> None:
        self.readings: dict[str, list[int]] = defaultdict(list)

    def measure(self, case: str, start: int) -> None:
        self.readings[case].append(time.perf_counter_ns() - start)

    def save(self, out: Path, version: str, redis_version: str, cpu: float) -> None:
        with (out / "raw.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("case", "sample", "duration_ns"))
            for name, samples in sorted(self.readings.items()):
                for index, nanoseconds in enumerate(samples):
                    writer.writerow((name, index, nanoseconds))
        cases: dict[str, object] = {}
        for name, values in sorted(self.readings.items()):
            readings = sorted(values)
            if len(readings) < 100:
                raise RuntimeError(f"Too few samples to compare {name}")
            cases[name] = {
                "samples": len(readings),
                "p50_ms": readings[math.ceil(len(readings) * .50) - 1] / 1e6,
                "p95_ms": readings[math.ceil(len(readings) * .95) - 1] / 1e6,
                "p99_ms": readings[math.ceil(len(readings) * .99) - 1] / 1e6,
                "mean_ms": statistics.mean(readings) / 1e6,
            }
        summary = {
            "metadata": {
                "cache_distribution": version,
                "python": platform.python_version(),
                "fastapi": metadata.version("fastapi"),
                "pydantic": metadata.version("pydantic"),
                "redis_py": metadata.version("redis"),
                "redis_server": redis_version,
                "process_cpu_seconds": cpu,
                "method": "ASGITransport and direct backend; fixed 120 HTTP / 1200 backend",
                "scope": "shared 0.5.0/0.6.0 features only, no production-network claims",
            },
            "cases": cases,
        }
        (out / "summary.json").write_text(
            json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )


def check_install(version: str) -> None:
    if metadata.version("fastapi-cache-stable") != version:
        raise RuntimeError("Wrong installed distribution version")
    try:
        metadata.distribution("fastapi-cache2")
    except metadata.PackageNotFoundError:
        pass
    else:
        raise RuntimeError("fastapi-cache2 must not be co-installed")
    path = Path(fastapi_cache.__file__).resolve()
    prefix = Path(sys.prefix).resolve()
    if not path.is_relative_to(prefix) or "site-packages" not in path.parts:
        raise RuntimeError("Import resolved outside isolated wheel site-packages")


async def inmemory_operations(rec: Recorder) -> None:
    backend = InMemoryBackend()  # Unbounded common API; not 0.6-only max_entries.
    payload = b"x" * 512
    namespace = "hist-" + uuid.uuid4().hex
    try:
        for index in range(1200):
            start = time.perf_counter_ns()
            await backend.set(f"{namespace}:item:{index}", payload, expire=60)
            rec.measure("inmemory_unbounded_set_512b", start)
        for index in range(1200):
            start = time.perf_counter_ns()
            value = await backend.get(f"{namespace}:item:{index}")
            rec.measure("inmemory_unbounded_get_512b", start)
            if value != payload:
                raise RuntimeError("InMemory bytes mismatch")
    finally:
        await backend.clear(namespace=namespace)


async def http_operations(rec: Recorder, backend: object, label: str) -> None:
    prefix = "hist-" + uuid.uuid4().hex
    FastAPICache.reset()
    FastAPICache.init(backend, prefix=prefix)
    app = FastAPI()

    @app.get("/value/{size}")
    @cache(namespace="plain", expire=60)
    async def value(size: str, nonce: int = 0) -> dict[str, object]:
        return {"data": "x" * (128 if size == "small" else 4096), "nonce": nonce}

    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://historical.invalid"
        ) as client:
            for size in ("small", "medium"):
                fixed = f"/value/{size}?nonce=0"
                warmup = await client.get(fixed)
                if warmup.status_code != 200 or warmup.headers.get(
                    "X-FastAPI-Cache"
                ) != "MISS":
                    raise RuntimeError("Common HTTP cache MISS not observed")
                etag = warmup.headers.get("ETag")
                if not etag:
                    raise RuntimeError("Published version lacks expected ETag")
                # Burn-in is identical between versions and not timed.
                for _ in range(20):
                    await client.get(fixed)
                for index in range(120):
                    for label_kind, target, headers, expected_status, expected_cache in (
                        ("hit", fixed, {}, 200, "HIT"),
                        ("miss", f"/value/{size}?nonce={index + 1}", {}, 200, "MISS"),
                        ("304", fixed, {"If-None-Match": etag}, 304, "HIT"),
                    ):
                        start = time.perf_counter_ns()
                        result = await client.get(target, headers=headers)
                        rec.measure(f"http_{label}_{label_kind}_{size}", start)
                        if (
                            result.status_code != expected_status
                            or result.headers.get("X-FastAPI-Cache") != expected_cache
                        ):
                            raise RuntimeError(
                                f"Different HTTP contract: {label_kind}, {size}"
                            )
    finally:
        try:
            await FastAPICache.clear()  # random prefix, all HTTP namespaces
        finally:
            FastAPICache.reset()


async def redis_operations(rec: Recorder, url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "redis" or parsed.hostname not in ("localhost", "127.0.0.1", "::1")
        or parsed.path != "/15" or parsed.port is None
        or parsed.username or parsed.password or parsed.query or parsed.fragment
    ):
        raise RuntimeError("Only credential-free Redis loopback /15 is allowed")
    client = Redis.from_url(url, decode_responses=False)
    try:
        info = await client.info("server")
        redis_version = str(info["redis_version"])
        if not redis_version.startswith("7.4."):
            raise RuntimeError("Comparison requires Redis 7.4 standalone")
        backend = RedisBackend(client)
        await http_operations(rec, backend, "redis")
        prefix = "hist-" + uuid.uuid4().hex
        payload = b"x" * 512
        try:
            for index in range(1200):
                key = f"{prefix}:item:{index}"
                start = time.perf_counter_ns()
                await backend.set(key, payload, expire=60)
                rec.measure("redis_set_512b", start)
            for index in range(1200):
                key = f"{prefix}:item:{index}"
                start = time.perf_counter_ns()
                result = await backend.get(key)
                rec.measure("redis_get_512b", start)
                if result != payload:
                    raise RuntimeError("Redis bytes mismatch")
        finally:
            await backend.clear(namespace=prefix)
        return redis_version
    finally:
        await client.aclose()


async def benchmark(rec: Recorder, url: str) -> str:
    await inmemory_operations(rec)
    await http_operations(rec, InMemoryBackend(), "inmemory")
    return await redis_operations(rec, url)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", choices=("0.5.0", "0.6.0"), required=True)
    parser.add_argument("--redis-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check_install(args.expected_version)
    args.output.mkdir(parents=True, exist_ok=True)
    rec = Recorder()
    started = time.process_time()
    redis_version = asyncio.run(benchmark(rec, args.redis_url))
    rec.save(args.output, args.expected_version, redis_version, time.process_time() - started)


if __name__ == "__main__":
    main()

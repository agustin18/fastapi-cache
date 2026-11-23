"""Installed-only HTTP, bounded InMemory and standalone Redis baselines.

Invoked by runner.py with python -I from a separate virtualenv. Deliberately
not imported by library CI or installed as part of the distribution.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import importlib.metadata as metadata
import json
import math
import platform
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, Header
from redis.asyncio import Redis

import fastapi_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


def resource_footprint() -> dict[str, int | None]:
    """Linux process measurements; peak RSS is cumulative since process start."""
    current: int | None = None
    peak: int | None = None
    status = Path("/proc/self/status")
    if sys.platform == "linux" and status.is_file():
        for line in status.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                current = int(line.split()[1])
            elif line.startswith("VmHWM:"):
                peak = int(line.split()[1])
    return {"rss_kib": current, "peak_rss_kib": peak}


class Measurements:
    def __init__(self) -> None:
        self.samples: dict[str, list[int]] = defaultdict(list)
        self.wall_seconds: dict[str, float] = defaultdict(float)
        self.operations: dict[str, int] = defaultdict(int)
        self.stage_resources: dict[str, dict[str, object]] = {}

    def record(self, case: str, ns: int) -> None:
        self.samples[case].append(ns)

    def batch(self, case: str, operations: int, seconds: float) -> None:
        self.wall_seconds[case] += seconds
        self.operations[case] += operations

    def save(self, out: Path, extra: dict[str, object]) -> None:
        with (out / "raw.csv").open("w", newline="", encoding="utf-8") as dest:
            writer = csv.writer(dest)
            writer.writerow(("case", "sample", "duration_ns"))
            for case, readings in sorted(self.samples.items()):
                for index, ns in enumerate(readings):
                    writer.writerow((case, index, ns))
        cases: dict[str, object] = {}
        for case, readings in sorted(self.samples.items()):
            ordered = sorted(readings)
            if not ordered:
                raise RuntimeError(f"Missing measurements for {case}")
            def ms(rank: float, samples: list[int] = ordered) -> float:
                return samples[math.ceil(rank * len(samples)) - 1] / 1_000_000
            seconds = self.wall_seconds[case]
            cases[case] = {
                "samples": len(ordered),
                "p50_ms": ms(0.50), "p95_ms": ms(0.95), "p99_ms": ms(0.99),
                "wall_seconds": seconds if seconds else None,
                "throughput_ops_s": self.operations[case] / seconds if seconds else None,
            }
        extra["stage_resources"] = self.stage_resources
        document = {"metadata": extra, "cases": cases}
        (out / "summary.json").write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(document, indent=2, sort_keys=True))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def verify_installed() -> None:
    require(metadata.version("fastapi-cache-stable") == "0.6.0", "Wrong distribution version")
    try:
        metadata.distribution("fastapi-cache2")
    except metadata.PackageNotFoundError:
        pass
    else:
        raise RuntimeError("Refusing co-installed fastapi-cache2")
    path = Path(fastapi_cache.__file__).resolve()
    prefix = Path(sys.prefix).resolve()
    require(path.is_relative_to(prefix) and "site-packages" in path.parts,
            f"Not importing installed wheel from virtualenv: {path}")


async def inmemory_cases(rec: Measurements, profile: str) -> None:
    capacities = (1000,) if profile == "smoke" else (1000, 10000, 100000)
    value = b"x" * 512
    for capacity in capacities:
        stage_cpu_start = time.process_time()
        backend = InMemoryBackend(max_entries=capacity)
        for stage in ("fill", "lru_churn", "read"):
            start = time.perf_counter()
            for index in range(capacity):
                if stage == "read":
                    key = f"lru_churn:{index}"
                    t = time.perf_counter_ns()
                    found = await backend.get(key)
                    rec.record(f"inmemory_{stage}_n{capacity}", time.perf_counter_ns() - t)
                    require(found == value, "Unexpected InMemory read")
                else:
                    key = f"{stage}:{index}"
                    t = time.perf_counter_ns()
                    await backend.set(key, value, expire=60)
                    rec.record(f"inmemory_{stage}_n{capacity}", time.perf_counter_ns() - t)
            elapsed = time.perf_counter() - start
            rec.batch(f"inmemory_{stage}_n{capacity}", capacity, elapsed)
        require(await backend.get("fill:0") is None, "LRU failed to evict old key")
        ttl = InMemoryBackend(max_entries=2)
        await ttl.set("expire:old", value, expire=1)
        await asyncio.sleep(2.2)  # integer-clock TTL uses strict <; allow a full extra second
        start = time.perf_counter_ns()
        await ttl.set("expire:fresh", value, expire=60)
        rec.record(f"inmemory_ttl_reclaim_n{capacity}", time.perf_counter_ns() - start)
        require(await ttl.get("expire:old") is None, "Expired item was returned")
        rec.stage_resources[f"inmemory_n{capacity}"] = {
            **resource_footprint(),
            "process_cpu_seconds": time.process_time() - stage_cpu_start,
            "scope": "process snapshot: cumulative peak RSS; CPU includes this capacity",
        }


async def http_cases(rec: Measurements, backend: object, label: str,
                     iterations: int) -> None:
    FastAPICache.reset()
    stage_cpu_start = time.process_time()
    FastAPICache.init(backend, prefix="perf-" + uuid.uuid4().hex)
    app = FastAPI()
    sizes = {"small": 128, "medium": 4096, "large": 65536}

    @app.get("/payload/{size}")
    @cache(namespace="payload", expire=60)
    async def payload(size: str, nonce: int = 0) -> dict[str, object]:
        return {"data": "x" * sizes[size], "nonce": nonce}

    @app.get("/vary")
    @cache(namespace="vary", expire=60, vary_headers=("Accept-Language",))
    async def vary(language: str = Header(default="en", alias="Accept-Language")) -> dict[str, str]:
        return {"language": language}

    @app.get("/ttl")
    @cache(namespace="ttl", expire=1)
    async def ttl() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/slow")
    @cache(namespace="slow", expire=60)
    async def slow(nonce: int = 0) -> dict[str, int]:
        await asyncio.sleep(0.01)
        return {"nonce": nonce}

    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://bench.invalid") as client:
            async def request(case: str, path: str, expected: str | None,
                              headers: dict[str, str] | None = None,
                              code: int = 200) -> httpx.Response:
                start = time.perf_counter_ns()
                response = await client.get(path, headers=headers)
                rec.record(f"http_{label}_{case}", time.perf_counter_ns() - start)
                require(response.status_code == code, f"Wrong HTTP status for {case}")
                if expected:
                    require(response.headers.get("X-FastAPI-Cache") == expected,
                            f"Unexpected {case} cache status: {response.headers.get('X-FastAPI-Cache')}")
                return response

            for size in (("small",) if iterations < 30 else sizes):
                fixed = f"/payload/{size}?nonce=99999"
                await request(f"warmup_{size}", fixed, "MISS")
                for i in range(iterations):
                    await request(f"hit_{size}", fixed, "HIT")
                    await request(f"miss_{size}", f"/payload/{size}?nonce={i + 1000}", "MISS")
                baseline = await client.get(fixed)
                etag = baseline.headers["etag"]
                for _i in range(iterations):
                    await request(f"304_{size}", fixed, "HIT",
                                  headers={"If-None-Match": etag}, code=304)
            await request("vary_warmup", "/vary", "MISS", {"Accept-Language": "en"})
            for _i in range(iterations):
                await request("vary_hit", "/vary", "HIT", {"Accept-Language": "en"})
                await request("auth_bypass", "/payload/small?nonce=99999", None,
                              {"Authorization": "Bearer synthetic-benchmark"})
            for i in range(max(3, iterations // 8)):
                await request("slow_miss", f"/slow?nonce={i}", "MISS")
            await request("slow_warmup", "/slow?nonce=99999", "MISS")
            for _i in range(iterations):
                await request("slow_hit", "/slow?nonce=99999", "HIT")
            await request("ttl_initial", "/ttl", "MISS")
            await asyncio.sleep(2.2)  # integer-clock TTL uses strict <; allow a full extra second
            await request("ttl_expired", "/ttl", "MISS")
            t = time.perf_counter_ns()
            removed = await FastAPICache.clear(namespace="payload")
            rec.record(f"http_{label}_clear_namespace", time.perf_counter_ns() - t)
            require(removed > 0, "Expected only benchmark namespace entries to clear")
            await request("after_clear", "/payload/small?nonce=99999", "MISS")
    finally:
        try:
            # Remove all HTTP namespaces (payload, vary, slow and TTL), not only
            # the payload namespace. The prefix is random and scoped to this run.
            await FastAPICache.clear()
        finally:
            rec.stage_resources[f"http_{label}"] = {
                **resource_footprint(),
                "process_cpu_seconds": time.process_time() - stage_cpu_start,
                "scope": "ASGI in-process HTTP; RSS high water includes previous stages",
            }
            FastAPICache.reset()


async def redis_cases(rec: Measurements, url: str, profile: str) -> dict[str, object]:
    parsed = urlsplit(url)
    require(parsed.scheme == "redis" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
            and parsed.path == "/15" and parsed.port is not None and not parsed.password,
            "Redis target must be localhost database 15")
    redis = Redis.from_url(url, decode_responses=False)
    stage_cpu_start = time.process_time()
    try:
        require(bool(await redis.ping()), "Redis ping failed")
        info = await redis.info("server")
        version = str(info["redis_version"])
        require(version.startswith("7.4."), f"Expected standalone Redis 7.4, got {version}")
        backend = RedisBackend(redis)
        server_cpu_start = await redis.info("cpu")
        server_memory_start = await redis.info("memory")
        await http_cases(rec, backend, "redis", 12 if profile == "smoke" else 100)
        prefix = "perf-" + uuid.uuid4().hex
        levels = (1, 10) if profile == "smoke" else (1, 10, 100, 1000)
        batches = 2 if profile == "smoke" else 4
        value = b"x" * 512
        for level in levels:
            async def operation(index: int, kind: str, batch: int, current_level: int = level) -> None:
                key = f"{prefix}:c{current_level}:{batch}:{index}"
                t = time.perf_counter_ns()
                if kind == "set":
                    await backend.set(key, value, expire=60)
                else:
                    require(await backend.get(key) == value, "Redis value mismatch")
                rec.record(f"redis_{kind}_concurrency_{current_level}", time.perf_counter_ns() - t)

            try:
                for batch in range(batches):
                    for kind in ("set", "get"):
                        t = time.perf_counter()
                        await asyncio.gather(*(operation(i, kind, batch) for i in range(level)))
                        rec.batch(f"redis_{kind}_concurrency_{level}", level,
                                  time.perf_counter() - t)
            finally:
                await backend.clear(namespace=prefix)
        server_cpu_end = await redis.info("cpu")
        server_memory_end = await redis.info("memory")
        rec.stage_resources["redis"] = {
            **resource_footprint(),
            "process_cpu_seconds": time.process_time() - stage_cpu_start,
            "redis_used_memory_start_bytes": int(server_memory_start["used_memory"]),
            "redis_used_memory_end_bytes": int(server_memory_end["used_memory"]),
            "redis_server_cpu_user_delta_seconds": (
                float(server_cpu_end["used_cpu_user"]) - float(server_cpu_start["used_cpu_user"])
            ),
            "redis_server_cpu_sys_delta_seconds": (
                float(server_cpu_end["used_cpu_sys"]) - float(server_cpu_start["used_cpu_sys"])
            ),
            "scope": "shared Redis INFO deltas (only isolated CI service gives attribution)",
        }
        return {"redis_server_version": version, "redis_profile": "standalone loopback /15"}
    finally:
        await redis.aclose()


async def execute(rec: Measurements, url: str, profile: str) -> dict[str, object]:
    await inmemory_cases(rec, profile)
    await http_cases(rec, InMemoryBackend(max_entries=1000), "inmemory",
                     12 if profile == "smoke" else 100)
    return await redis_cases(rec, url, profile)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "full"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--redis-url", required=True)
    args = parser.parse_args()
    verify_installed()
    args.output.mkdir(parents=True, exist_ok=True)
    rec = Measurements()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    details = asyncio.run(execute(rec, args.redis_url, args.profile))
    metadata_record: dict[str, object] = {
        "scope": "in-process ASGITransport (not HTTP network), direct backend operations",
        "profile": args.profile,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cache_distribution": metadata.version("fastapi-cache-stable"),
        "fastapi": metadata.version("fastapi"),
        "redis_py": metadata.version("redis"),
        "httpx": metadata.version("httpx"),
        "payload_bytes": {"small": 128, "medium": 4096, "large": 65536,
                          "direct_backend": 512},
        "sampling": "nearest-rank percentiles over individual operation durations",
        "resource_usage": {
            **resource_footprint(),
            "process_cpu_seconds": time.process_time() - cpu_start,
            "process_wall_seconds": time.perf_counter() - wall_start,
            "scope": "one fresh Python process (imports, InMemory, HTTP, Redis); Linux /proc RSS",
        },
        "rss_note": "Peak RSS cumulative across whole process; NOT per-backend memory; entries are not byte caps",
        "limitations": "No TLS, Cluster, Sentinel, HA, failure injection, external HTTP network or historical comparisons",
        **details,
    }
    rec.save(args.output, metadata_record)


if __name__ == "__main__":
    main()

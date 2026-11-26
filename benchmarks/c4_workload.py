"""C4 descriptive comparison of installed cache versions on one host.

Run only on Python 3.12 with disposable loopback Redis DB15. Each invocation
is an independent process. No timing threshold or performance certification.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import importlib.metadata as metadata
import importlib.util
import json
import math
import platform
import resource
import socket
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import uvicorn
from fastapi import FastAPI, Header
from redis.asyncio import Redis

import fastapi_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


def _load_expected_version_reader():
    # The workload runs with python -I, so the sibling helper is not importable
    # through sys.path; load it from the exact script directory instead.
    path = Path(__file__).with_name("c4_versions.py")
    spec = importlib.util.spec_from_file_location("c4_versions", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load C4 version helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.expected_distribution_version


expected_distribution_version = _load_expected_version_reader()

MODES = ("published", "candidate-legacy", "scoped-off", "scoped-on")
SAMPLES = 120
WARMUP = 20
CONCURRENCY = 8


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_install(mode: str, candidate_version: str | None = None) -> None:
    location = Path(fastapi_cache.__file__).resolve()
    require("site-packages" in location.parts and location.is_relative_to(Path(sys.prefix)),
            "Expected isolated installed cache distribution")
    expected = expected_distribution_version(mode, candidate_version)
    require(metadata.version("fastapi-cache-stable") == expected, "Unexpected distribution metadata")
    require(hasattr(fastapi_cache, "CacheFailurePolicy") == (mode != "published"),
            "Wrong wheel for requested comparison mode")
    try:
        metadata.distribution("fastapi-cache2")
    except metadata.PackageNotFoundError:
        pass
    else:
        raise RuntimeError("Conflicting import owner")


def validate_redis(url: str) -> None:
    p = urlsplit(url)
    require(
        p.scheme == "redis" and p.hostname == "127.0.0.1" and p.port is not None
        and p.path == "/15" and p.username is None and p.password is None
        and not p.query and not p.fragment,
        "Use disposable loopback Redis DB15 only",
    )


def rank(values: list[int], quantile: float) -> float:
    return sorted(values)[math.ceil(len(values) * quantile) - 1] / 1e6


def make_app(options: dict[str, Any]) -> FastAPI:
    app = FastAPI()

    @app.get("/payload/{size}")
    @cache(namespace="payload", expire=300, **options)
    async def payload(size: int, nonce: int = 0) -> dict[str, Any]:
        return {"data": "x" * size, "nonce": nonce}

    @app.get("/vary")
    @cache(namespace="vary", expire=300, vary_headers=["Accept-Language"], **options)
    async def vary(language: str = Header(default="en", alias="Accept-Language")) -> dict[str, str]:
        return {"language": language}

    @app.get("/slow")
    @cache(namespace="slow", expire=300, **options)
    async def slow(nonce: int = 0) -> dict[str, int]:
        await asyncio.sleep(0.005)
        return {"nonce": nonce}

    return app


async def exercise(client: httpx.AsyncClient, label: str,
                   raw: list[tuple[str, int, int]]) -> dict[str, Any]:
    cases: dict[str, Any] = {}

    async def request(path: str, expected: str | None, code: int = 200,
                      headers: dict[str, str] | None = None) -> tuple[int, httpx.Response]:
        start = time.perf_counter_ns()
        result = await client.get(path, headers=headers)
        elapsed = time.perf_counter_ns() - start
        require(result.status_code == code, "Unexpected HTTP status: " + label)
        require(result.headers.get("X-FastAPI-Cache") == expected, "Unexpected cache status: " + label)
        return elapsed, result

    async def serial(name: str, path: str, expected: str | None, *,
                     code: int = 200, headers: dict[str, str] | None = None,
                     unique: bool = False, body_size: int | None = None) -> None:
        values: list[int] = []
        wall = time.perf_counter_ns()
        for i in range(WARMUP + SAMPLES):
            target = path + ("?nonce=" + str(i + 1) if unique else "")
            if i == WARMUP:
                wall = time.perf_counter_ns()
            elapsed, response = await request(target, expected, code, headers)
            if body_size is not None:
                require(len(response.json()["data"]) == body_size, "Wrong payload")
                require(response.json()["nonce"] == (i + 1 if unique else 0), "Wrong nonce")
            if i >= WARMUP:
                values.append(elapsed)
        duration = time.perf_counter_ns() - wall
        record(name, values, duration)

    def record(name: str, values: list[int], duration: int) -> None:
        key = label + "/" + name
        raw.extend((key, i, value) for i, value in enumerate(values))
        cases[key] = {
            "samples": len(values), "p50_ms": rank(values, .50),
            "p95_ms": rank(values, .95), "p99_ms": rank(values, .99),
            "requests_per_second": len(values) * 1e9 / duration,
        }

    for size in (128, 4096, 65536):
        _, seeded = await request(f"/payload/{size}", "MISS")
        require(len(seeded.json()["data"]) == size, "Wrong seed payload")
        await serial(f"hit-{size}", f"/payload/{size}", "HIT", body_size=size)
    _, hit = await request("/payload/128", "HIT")
    await serial("conditional", "/payload/128", "HIT", code=304,
                 headers={"If-None-Match": hit.headers["ETag"]})
    await serial("cold-miss", "/payload/128", "MISS", unique=True, body_size=128)
    await serial("auth-bypass", "/payload/128", None,
                 headers={"Authorization": "Bearer synthetic"}, body_size=128)
    for lang in ("en", "es"):
        _, variant = await request("/vary", "MISS", headers={"Accept-Language": lang})
        require(variant.json()["language"] == lang, "Wrong Vary seed")
    await serial("vary-hit", "/vary", "HIT", headers={"Accept-Language": "es"})
    await serial("slow-miss", "/slow", "MISS", unique=True)

    async def batch() -> list[tuple[int, httpx.Response]]:
        return await asyncio.gather(*(request("/payload/128", "HIT") for _ in range(CONCURRENCY)))

    await batch()
    await batch()
    values: list[int] = []
    wall = time.perf_counter_ns()
    for _ in range(SAMPLES // CONCURRENCY):
        values.extend(elapsed for elapsed, _ in await batch())
    record("concurrent-hit-8", values, time.perf_counter_ns() - wall)
    return cases


async def run_one(mode: str, backend_name: str, transport: str,
                  url: str, raw: list[tuple[str, int, int]]) -> tuple[dict[str, Any], dict[str, float]]:
    prefix = "c4-bench-" + uuid.uuid4().hex
    redis = Redis.from_url(url, decode_responses=False) if backend_name == "redis" else None
    backend: Any = RedisBackend(redis) if redis is not None else InMemoryBackend()
    scoped = mode.startswith("scoped-")
    app = make_app({"scope": "app"} if scoped else {})
    handle: Any = None
    started = time.perf_counter_ns()
    if scoped:
        from fastapi_cache import CacheConfig, CacheFailurePolicy, CacheHandle

        config = CacheConfig(
            backend, scope_id=prefix, expire=300,
            failure_policy=CacheFailurePolicy(
                strict_read=mode == "scoped-on", conservative_write=mode == "scoped-on",
                recover_json=mode == "scoped-on",
            ),
        )
        handle = CacheHandle(config)
        await handle.start(app)
    else:
        FastAPICache.reset()
        FastAPICache.init(backend, prefix=prefix, expire=300)
    init_ms = (time.perf_counter_ns() - started) / 1e6
    task = None
    sock = None
    server = None
    try:
        if transport == "tcp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sock.listen(128)
            server = uvicorn.Server(uvicorn.Config(
                app, log_level="error", access_log=False, lifespan="off",
            ))
            task = asyncio.create_task(server.serve(sockets=[sock]))
            deadline = time.monotonic() + 10
            while not server.started:
                require(not task.done() and time.monotonic() < deadline, "TCP startup failed")
                await asyncio.sleep(.01)
            client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{sock.getsockname()[1]}",
                                       trust_env=False, timeout=10)
        else:
            client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                       base_url="http://test", trust_env=False)
        async with client:
            cases = await exercise(client, backend_name + "/" + transport, raw)
    finally:
        if server is not None and task is not None:
            server.should_exit = True
            await asyncio.wait_for(task, 10)
        if sock is not None:
            sock.close()
        if scoped:
            await handle.clear()
        else:
            await FastAPICache.clear()
        started = time.perf_counter_ns()
        if scoped:
            await handle.aclose()
        else:
            FastAPICache.reset()
        close_ms = (time.perf_counter_ns() - started) / 1e6
        if redis is not None:
            root = "__fastapi_cache_app_v1__:" + prefix if scoped else prefix
            try:
                require(not [key async for key in redis.scan_iter(match=root + ":*")],
                        "Benchmark left scoped Redis entries")
            finally:
                await redis.aclose()
    return cases, {"init_ms": init_ms, "close_ms": close_ms}


async def main_async(args: argparse.Namespace) -> None:
    verify_install(args.mode, args.candidate_version)
    validate_redis(args.redis_url)
    raw: list[tuple[str, int, int]] = []
    cases: dict[str, Any] = {}
    lifecycle: dict[str, Any] = {}
    cpu = time.process_time()
    wall = time.perf_counter()
    for backend in ("inmemory", "redis"):
        for transport in ("asgi", "tcp"):
            result, times = await run_one(args.mode, backend, transport, args.redis_url, raw)
            cases.update(result)
            lifecycle[backend + "/" + transport] = times
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "raw.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case", "sample", "duration_ns"])
        writer.writerows(raw)
    summary = {
        "mode": args.mode, "cases": cases, "lifecycle": lifecycle,
        "cpu_seconds": time.process_time() - cpu,
        "wall_seconds": time.perf_counter() - wall,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "python": platform.python_version(), "platform": platform.platform(),
        "transport_note": "ASGI and real TCP loopback; TCP client/server share process and loop",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-version", default=None)
    parser.add_argument("--redis-url", default="redis://127.0.0.1:6379/15")
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()

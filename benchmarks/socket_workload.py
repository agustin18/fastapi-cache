"""Real loopback TCP HTTP baseline against the SHA-verified published 0.6.0 wheel.

Two isolated server processes (InMemory and Redis), with httpx over a REAL
127.0.0.1 socket. Never fetches a remote service, never flushes a Redis DB.
This is a descriptive GitHub-runner profile, not fixed-hardware certification.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import importlib.metadata as metadata
import json
import math
import os
import platform
import socket
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path
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


def installed_only() -> None:
    if metadata.version("fastapi-cache-stable") != "0.6.0":
        raise RuntimeError("Wrong published wheel version")
    try:
        metadata.distribution("fastapi-cache2")
    except metadata.PackageNotFoundError:
        pass
    else:
        raise RuntimeError("Refusing shared fastapi_cache import owners")
    imported = Path(fastapi_cache.__file__).resolve()
    if "site-packages" not in imported.parts or not imported.is_relative_to(
        Path(sys.prefix).resolve()
    ):
        raise RuntimeError("Refusing non-wheel fastapi_cache import")


def check_redis(value: str) -> str:
    p = urlsplit(value)
    if (
        p.scheme != "redis"
        or p.hostname not in ("localhost", "127.0.0.1", "::1")
        or p.port is None
        or p.path != "/15"
        or p.username is not None
        or p.password is not None
        or p.query
        or p.fragment
    ):
        raise ValueError("Only loopback Redis DB15 without credentials is permitted")
    return value


def create_app(backend: object, prefix: str) -> FastAPI:
    FastAPICache.init(backend, prefix=prefix)
    app = FastAPI()
    sizes = {"small": 128, "medium": 4096, "large": 65536}

    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ready": True}

    @app.get("/payload/{size}")
    @cache(namespace="net-payload", expire=60)
    async def payload(size: str, nonce: int = 0) -> dict[str, object]:
        if size not in sizes:
            return {"error": "invalid synthetic payload size"}
        return {"data": "x" * sizes[size], "nonce": nonce}

    @app.get("/vary")
    @cache(namespace="net-vary", expire=60, vary_headers=("Accept-Language",))
    async def vary(
        language: str = Header(default="en", alias="Accept-Language"),
    ) -> dict[str, str]:
        return {"language": language}

    @app.get("/slow")
    @cache(namespace="net-slow", expire=60)
    async def slow(nonce: int = 0) -> dict[str, int]:
        await asyncio.sleep(0.005)
        return {"nonce": nonce}

    @app.get("/ttl")
    @cache(namespace="net-ttl", expire=1)
    async def ttl() -> dict[str, bool]:
        return {"ok": True}

    return app


async def serve(args: argparse.Namespace) -> None:
    installed_only()
    client: Redis | None = None
    try:
        if args.backend == "redis":
            client = Redis.from_url(check_redis(args.redis_url), decode_responses=False)
            if not await client.ping():
                raise RuntimeError("Disposable Redis did not respond")
            backend: object = RedisBackend(client)
        else:
            backend = InMemoryBackend()
        app = create_app(backend, args.prefix)
        server = uvicorn.Server(
            uvicorn.Config(
                app, host="127.0.0.1", port=args.port, access_log=False,
                log_level="error", lifespan="off", workers=1,
            )
        )
        await server.serve()
    finally:
        FastAPICache.reset()
        if client is not None:
            await client.aclose()


class Samples:
    def __init__(self) -> None:
        self.values: dict[str, list[int]] = defaultdict(list)

    def record(self, name: str, elapsed: int) -> None:
        self.values[name].append(elapsed)

    def save(self, output: Path) -> None:
        with (output / "raw.csv").open("w", newline="", encoding="utf-8") as stream:
            csvout = csv.writer(stream)
            csvout.writerow(["case", "sample", "duration_ns"])
            for case, values in sorted(self.values.items()):
                for index, duration in enumerate(values):
                    csvout.writerow([case, index, duration])

        def rank(values: list[int], fraction: float) -> float:
            return sorted(values)[math.ceil(len(values) * fraction) - 1] / 1e6

        cases: dict[str, object] = {}
        for case, values in sorted(self.values.items()):
            if len(values) < 100:
                raise RuntimeError("Too few samples for " + case)
            cases[case] = {
                "samples": len(values),
                "p50_ms": rank(values, .50),
                "p95_ms": rank(values, .95),
                "p99_ms": rank(values, .99),
            }
        summary = {
            "metadata": {
                "published_version": metadata.version("fastapi-cache-stable"),
                "fastapi": metadata.version("fastapi"),
                "httpx": metadata.version("httpx"),
                "uvicorn": metadata.version("uvicorn"),
                "redis_py": metadata.version("redis"),
                "python": platform.python_version(),
                "platform": platform.platform(),
                "transport": "real TCP loopback HTTP, separate Uvicorn OS process",
                "isolation": "installed published wheel, python -I, no editable install",
                "tail_warning": (
                    "Nearest-rank p99 across serial requests on a shared "
                    "runner is descriptive only; not a production p99 estimate"
                ),
            },
            "cases": cases,
        }
        (output / "summary.json").write_text(
            json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )


def unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def cleanup_redis(url: str, prefix: str) -> None:
    """Remove *only* the random benchmark prefix; no FLUSHDB/other tenants."""
    redis = Redis.from_url(check_redis(url), decode_responses=False)
    try:
        keys = [key async for key in redis.scan_iter(match=prefix + ":*")]
        for offset in range(0, len(keys), 200):
            await redis.unlink(*keys[offset:offset + 200])
        if [key async for key in redis.scan_iter(match=prefix + ":*")]:
            raise RuntimeError("Socket benchmark left its Redis prefix behind")
    finally:
        await redis.aclose()


async def exercise(
    client: httpx.AsyncClient, label: str, iterations: int, rec: Samples
) -> None:
    async def request(
        case: str | None, url: str, cache_status: str | None,
        headers: dict[str, str] | None = None, code: int = 200,
    ) -> httpx.Response:
        start = time.perf_counter_ns()
        result = await client.get(url, headers=headers)
        elapsed = time.perf_counter_ns() - start
        if case is not None:
            rec.record("socket_" + label + "_" + case, elapsed)
        if result.status_code != code:
            raise RuntimeError("Invalid HTTP response for " + url)
        status = result.headers.get("X-FastAPI-Cache")
        if status != cache_status:
            raise RuntimeError("Invalid cache status for " + url)
        if code == 304 and result.content:
            raise RuntimeError("304 returned a body")
        return result

    for size in ("small", "medium", "large"):
        fixed = "/payload/" + size + "?nonce=777"
        first = await request(None, fixed, "MISS")
        tag = first.headers["etag"]
        await request(None, fixed, "HIT")
        for index in range(iterations):
            await request("hit_" + size, fixed, "HIT")
            await request(
                "miss_" + size, f"/payload/{size}?nonce={index + 1000}", "MISS"
            )
            await request(
                "304_" + size, fixed, "HIT",
                headers={"If-None-Match": tag}, code=304,
            )

    await request(None, "/vary", "MISS", {"Accept-Language": "en"})
    await request(None, "/vary", "MISS", {"Accept-Language": "de"})
    await request(None, "/vary", "HIT", {"Accept-Language": "en"})

    for index in range(iterations):
        await request(
            "auth_bypass", "/payload/small?nonce=777", None,
            {"Authorization": "Bearer synthetic-test-only"},
        )
    await request(None, "/slow?nonce=31415", "MISS")
    for _ in range(iterations):
        await request("slow_hit", "/slow?nonce=31415", "HIT")

    await request(None, "/ttl", "MISS")
    await asyncio.sleep(2.2)  # 0.6.0 integer wall-clock strict < expiry
    await request(None, "/ttl", "MISS")


async def run_one(
    args: argparse.Namespace, backend: str, rec: Samples
) -> None:
    prefix = "perf-http-" + uuid.uuid4().hex
    port = unused_port()
    output = Path(args.output)
    log = output / ("socket-server-" + backend + ".log")
    command = [
        sys.executable, "-I", str(Path(__file__).resolve()), "serve",
        "--backend", backend, "--redis-url", args.redis_url,
        "--port", str(port), "--prefix", prefix,
    ]
    # Only synthetic requests; Uvicorn access logs are disabled.
    with log.open("w", encoding="utf-8") as errors:
        process = subprocess.Popen(  # noqa: S603 - fixed isolated interpreter
            command, stdin=subprocess.DEVNULL, stdout=errors,
            stderr=subprocess.STDOUT, cwd=str(output),
            env={**os.environ, "PYTHONNOUSERSITE": "1"},
        )
        try:
            async with httpx.AsyncClient(
                base_url=f"http://127.0.0.1:{port}",
                timeout=httpx.Timeout(5.0), trust_env=False,
            ) as client:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError("Uvicorn exited during socket startup")
                    try:
                        health = await client.get("/health")
                        if health.status_code == 200 and health.json() == {"ready": True}:
                            break
                    except httpx.TransportError:
                        pass
                    await asyncio.sleep(0.05)
                else:
                    raise RuntimeError("Socket server failed to listen on loopback")
                await exercise(client, backend, args.iterations, rec)
        finally:
            process.terminate() if process.poll() is None else None
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            if backend == "redis":
                await cleanup_redis(args.redis_url, prefix)


async def run(args: argparse.Namespace) -> None:
    installed_only()
    check_redis(args.redis_url)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    rec = Samples()
    for backend in ("inmemory", "redis"):
        await run_one(args, backend, rec)
    rec.save(output)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("serve", "run"))
    p.add_argument("--backend", choices=("redis", "inmemory"), default="inmemory")
    p.add_argument("--redis-url", default="redis://127.0.0.1:6379/15")
    p.add_argument("--port", type=int, default=0)
    p.add_argument("--prefix", default="")
    p.add_argument("--iterations", type=int, default=120)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if sys.version_info[:2] != (3, 12):
        p.error("This profile is calibrated for CPython 3.12 only")
    if args.mode == "serve":
        if args.port < 1024 or args.port > 65535 or not args.prefix.startswith("perf-http-"):
            p.error("Server requires random synthetic prefix and nonprivileged port")
        asyncio.run(serve(args))
    else:
        if args.output is None or not 100 <= args.iterations <= 1000:
            p.error("Runner requires an output directory and 100..1000 samples")
        asyncio.run(run(args))


if __name__ == "__main__":
    main()

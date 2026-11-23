"""Isolated installed-wheel Redis 7.4 stop/restart probe.

Requires explicit REDIS_FAULT_DISPOSABLE=1; creates and controls its own
uniquely named local Docker container. No external target or shared Redis.
"""
import asyncio
import importlib.metadata as metadata
import io
import logging
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

import fastapi_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


def docker(*args):
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=True, timeout=90,
    )
    return result.stdout.strip()


async def wait_ready(client):
    for _ in range(80):
        try:
            if await asyncio.wait_for(client.ping(), timeout=1.5):
                return
        except (RedisConnectionError, RedisTimeoutError, asyncio.TimeoutError):
            pass
        await asyncio.sleep(0.2)
    raise RuntimeError("Disposable Redis did not become healthy")


def assert_installed(expected):
    if metadata.version("fastapi-cache-stable") != expected:
        raise AssertionError("Wrong installed candidate distribution")
    path = Path(fastapi_cache.__file__).resolve()
    root = str(Path(sys.prefix).resolve()) + os.sep
    if "site-packages" not in path.parts or not str(path).startswith(root):
        raise AssertionError("Only a wheel installed inside this venv is allowed")
    try:
        metadata.version("fastapi-cache2")
    except metadata.PackageNotFoundError:
        return
    raise AssertionError("Conflicting fastapi_cache import owners")


async def exercise(name, port):
    client = Redis(
        host="127.0.0.1", port=port, db=15, decode_responses=False,
        socket_timeout=0.4, socket_connect_timeout=0.4,
        retry_on_timeout=False,
    )
    backend = RedisBackend(client)
    namespace = "fault-070-" + uuid.uuid4().hex
    key = namespace + ":direct"
    counter = [0]
    logstream = io.StringIO()
    logger = logging.getLogger("fastapi_cache.decorator")
    handler = logging.StreamHandler(logstream)
    logger.addHandler(handler)
    try:
        await wait_ready(client)
        FastAPICache.init(backend, prefix=namespace)

        @cache(namespace="probe", expire=45)
        async def compute():
            counter[0] += 1
            return {"count": counter[0]}

        await backend.set(key, b"sample", expire=45)
        assert await backend.get(key) == b"sample"
        assert await compute() == {"count": 1}
        assert await compute() == {"count": 1}
        assert counter == [1]

        docker("stop", "--time", "1", name)
        try:
            await asyncio.wait_for(backend.get_with_ttl(key), timeout=3.0)
        except (RedisConnectionError, RedisTimeoutError):
            pass
        else:
            raise AssertionError("Backend read unexpectedly succeeded during Redis outage")

        # Characterize existing read/write fallback; no new recovery policy.
        assert await asyncio.wait_for(compute(), timeout=3.0) == {"count": 2}
        responses = await asyncio.wait_for(
            asyncio.gather(*[compute() for _ in range(6)]), timeout=12.0,
        )
        assert len(responses) == 6
        assert len({item["count"] for item in responses}) == 6
        assert counter == [8]
        logs = logstream.getvalue()
        assert "Error retrieving cache entry" in logs
        assert "Error setting cache entry" in logs
        assert key not in logs
        assert "sample" not in logs

        docker("start", name)
        await wait_ready(client)
        # Ephemeral Redis explicitly disables snapshots/AOF.
        assert await backend.get(key) is None
        new = await asyncio.wait_for(compute(), timeout=3.0)
        assert new == {"count": 9}
        assert await compute() == new
        assert counter == [9]
        await backend.clear(key=key)
    finally:
        FastAPICache.reset()
        logger.removeHandler(handler)
        await client.aclose()


def main():
    if os.environ.get("REDIS_FAULT_DISPOSABLE") != "1":
        raise SystemExit("Refusing without REDIS_FAULT_DISPOSABLE=1")
    version = os.environ.get("CANDIDATE_VERSION", "")
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.dev[0-9]+)?", version) is None:
        raise SystemExit("Explicit tested CANDIDATE_VERSION is mandatory")
    assert_installed(version)
    name = "fastapi-cache-fault-070-" + uuid.uuid4().hex[:12]
    try:
        docker(
            "run", "-d", "--name", name, "-p", "127.0.0.1::6379",
            "redis:7.4", "redis-server", "--save", "", "--appendonly", "no",
        )
        mapping = docker("port", name, "6379/tcp")
        match = re.fullmatch(r"127\.0\.0\.1:(\d+)", mapping)
        if match is None:
            raise RuntimeError("Unsafe Docker port mapping")
        port = int(match.group(1))
        if not (1024 <= port <= 65535):
            raise RuntimeError("Unsafe port")
        asyncio.run(exercise(name, port))
    finally:
        try:
            docker("rm", "-f", name)
        except subprocess.CalledProcessError:
            pass
    print("PASS: installed-wheel Redis daemon stop/restart and recovery")


if __name__ == "__main__":
    main()

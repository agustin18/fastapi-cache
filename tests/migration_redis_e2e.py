"""Run each mode in its own virtualenv against one dedicated Redis database.

See MIGRATION.md for the legacy writer, candidate reader, and rollback sequence.
"""

from __future__ import annotations

import importlib.metadata
import os
import sys
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import AsyncGenerator

import redis
import redis.asyncio as redis_async
from fastapi import FastAPI, Request, Response
from starlette.testclient import TestClient

import fastapi_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

REDIS_URL = os.environ["REDIS_URL"]
PREFIX = os.environ["MIGRATION_E2E_PREFIX"]
GENERATION = os.environ.get("MIGRATION_E2E_GENERATION", "legacy")
TTL_SECONDS = 120
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

ordinary_calls = 0
private_calls = 0
special_calls = 0


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    client = redis_async.Redis.from_url(REDIS_URL)
    FastAPICache.init(RedisBackend(client), prefix=PREFIX)
    try:
        yield
    finally:
        try:
            await client.close(close_connection_pool=True)
        finally:
            reset = getattr(FastAPICache, "reset", None)
            if reset is not None:
                reset()


app = FastAPI(lifespan=lifespan)


@app.get("/ordinary")
@cache(namespace="ordinary", expire=TTL_SECONDS)
async def ordinary(response: Response) -> dict[str, str]:
    global ordinary_calls
    ordinary_calls += 1
    return {"generation": GENERATION, "kind": "ordinary"}


@app.get("/private")
@cache(namespace="private", expire=TTL_SECONDS)
async def private(request: Request, response: Response) -> dict[str, str]:
    global private_calls
    private_calls += 1
    return {
        "principal": request.headers.get("Authorization", "anonymous"),
        "kind": "private",
    }


@app.get("/special")
@cache(namespace="special", expire=TTL_SECONDS)
async def special(response: Response) -> date:
    global special_calls
    special_calls += 1
    return date(2026, 11, 17)


@app.post("/migration/cleanup")
async def cleanup_legacy_incompatible_namespaces() -> dict[str, int]:
    return {
        "private": await FastAPICache.clear(namespace="private"),
        "special": await FastAPICache.clear(namespace="special"),
    }


def _check_installed_distribution(mode: str) -> None:
    expected = (
        "fastapi-cache2"
        if mode in {"seed", "rollback"}
        else "fastapi-cache-stable"
    )
    other = (
        "fastapi-cache-stable"
        if expected == "fastapi-cache2"
        else "fastapi-cache2"
    )
    installed_version = importlib.metadata.version(expected)
    expected_version = (
        "0.2.2"
        if expected == "fastapi-cache2"
        else os.environ.get("MIGRATION_E2E_CANDIDATE_VERSION")
    )
    if expected_version is not None and installed_version != expected_version:
        raise AssertionError(f"Expected {expected}=={expected_version}")
    try:
        importlib.metadata.version(other)
    except importlib.metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError(
            f"Do not install both distributions: {expected} and {other}"
        )

    module_path = fastapi_cache.__file__
    assert module_path is not None
    if REPOSITORY_ROOT in Path(module_path).resolve().parents:
        raise AssertionError(
            f"Imported package from source checkout: {module_path}"
        )
    print(f"Installed distribution: {expected}=={installed_version}")
    print(f"Import location: {module_path}")


def _redis_keys(namespace: str) -> list[bytes]:
    client = redis.Redis.from_url(REDIS_URL)
    try:
        return list(client.scan_iter(match=f"{PREFIX}:{namespace}:*"))
    finally:
        client.close()


def _assert_ordinary_ttl() -> None:
    keys = _redis_keys("ordinary")
    assert len(keys) == 1
    client = redis.Redis.from_url(REDIS_URL)
    try:
        ttl = client.ttl(keys[0])
    finally:
        client.close()
    assert 0 < ttl <= TTL_SECONDS


def seed_legacy_data() -> None:
    if (
        _redis_keys("ordinary")
        or _redis_keys("private")
        or _redis_keys("special")
    ):
        raise AssertionError(
            f"Redis prefix {PREFIX!r} is not empty; choose a unique test prefix"
        )

    with TestClient(app) as client:
        ordinary_response = client.get("/ordinary")
        assert ordinary_response.headers["X-FastAPI-Cache"] == "MISS"
        assert ordinary_response.json() == {
            "generation": "legacy",
            "kind": "ordinary",
        }

        ordinary_hit = client.get("/ordinary")
        assert ordinary_hit.headers["X-FastAPI-Cache"] == "HIT"
        assert ordinary_hit.json() == ordinary_response.json()
        assert ordinary_calls == 1

        alice = client.get(
            "/private", headers={"Authorization": "Bearer Alice"}
        )
        bob = client.get("/private", headers={"Authorization": "Bearer Bob"})
        assert alice.headers["X-FastAPI-Cache"] == "MISS"
        assert bob.headers["X-FastAPI-Cache"] == "HIT"
        assert bob.json()["principal"] == "Bearer Alice"
        assert private_calls == 1

        special_response = client.get("/special")
        assert special_response.headers["X-FastAPI-Cache"] == "MISS"
        assert special_response.json() == "2026-11-17"
        assert client.get("/special").headers["X-FastAPI-Cache"] == "HIT"
        assert special_calls == 1

    _assert_ordinary_ttl()
    special_keys = _redis_keys("special")
    assert len(special_keys) == 1
    sync_client = redis.Redis.from_url(REDIS_URL)
    try:
        legacy_special_value = sync_client.get(special_keys[0])
    finally:
        sync_client.close()
    assert legacy_special_value is not None
    assert b"_spec_type" in legacy_special_value
    print(
        "Legacy writer: ordinary, authenticated and special-type entries persisted"
    )


def verify_candidate_migration() -> None:
    with TestClient(app) as client:
        cleanup_response = client.post("/migration/cleanup")
        cleanup_counts = cleanup_response.json()
        assert cleanup_counts["private"] >= 1
        assert cleanup_counts["special"] >= 1
        assert not _redis_keys("private")
        assert not _redis_keys("special")

        ordinary_response = client.get("/ordinary")
        assert ordinary_response.headers["X-FastAPI-Cache"] == "HIT"
        assert ordinary_response.json() == {
            "generation": "legacy",
            "kind": "ordinary",
        }
        assert ordinary_calls == 0
        max_age = int(
            ordinary_response.headers["Cache-Control"].split("=", 1)[1]
        )
        assert 0 < max_age <= TTL_SECONDS

        authenticated = client.get(
            "/private", headers={"Authorization": "Bearer Bob"}
        )
        assert "X-FastAPI-Cache" not in authenticated.headers
        assert authenticated.json()["principal"] == "Bearer Bob"
        assert private_calls == 1

        anonymous = client.get("/private")
        assert anonymous.headers["X-FastAPI-Cache"] == "MISS"
        assert anonymous.json()["principal"] == "anonymous"
        assert private_calls == 2

        special_response = client.get("/special")
        assert special_response.headers["X-FastAPI-Cache"] == "MISS"
        assert special_response.json() == "2026-11-17"
        assert special_calls == 1

        refreshed = client.get(
            "/ordinary", headers={"Cache-Control": "no-cache"}
        )
        assert refreshed.headers["X-FastAPI-Cache"] == "MISS"
        assert refreshed.json() == {
            "generation": "candidate",
            "kind": "ordinary",
        }
        assert client.get("/ordinary").headers["X-FastAPI-Cache"] == "HIT"
        assert ordinary_calls == 1
    print(
        "Candidate reader: legacy entries handled; private/special namespaces cleaned"
    )


def verify_rollback_read() -> None:
    with TestClient(app) as client:
        response = client.get("/ordinary")
    assert response.headers["X-FastAPI-Cache"] == "HIT"
    assert response.json() == {"generation": "candidate", "kind": "ordinary"}
    assert ordinary_calls == 0
    print("Legacy rollback reader: candidate ordinary entry remains readable")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {
        "seed",
        "candidate",
        "rollback",
    }:
        raise SystemExit(
            "Usage: migration_redis_e2e.py seed|candidate|rollback"
        )
    mode = sys.argv[1]
    _check_installed_distribution(mode)
    if mode == "seed":
        seed_legacy_data()
    elif mode == "candidate":
        verify_candidate_migration()
    else:
        verify_rollback_read()


if __name__ == "__main__":
    main()

"""Run each mode in its own virtualenv against one dedicated Redis database.

See MIGRATION.md for the legacy writer, candidate reader, and rollback sequence.
"""

from __future__ import annotations

import importlib.metadata
import os
import re
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

REDIS_URL = os.environ.get("REDIS_URL", "")
PREFIX = os.environ.get("MIGRATION_E2E_PREFIX", "")
GENERATION = os.environ.get("MIGRATION_E2E_GENERATION", "legacy")
TTL_SECONDS = 120
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

ordinary_calls = 0
private_calls = 0
special_calls = 0
unrelated_calls = 0


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


@app.get("/unrelated")
@cache(namespace="unrelated", expire=TTL_SECONDS)
async def unrelated(response: Response) -> dict[str, str]:
    global unrelated_calls
    unrelated_calls += 1
    return {"kind": "unrelated", "value": "must-survive-targeted-clear"}


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


def _prefix_keys() -> list[bytes]:
    client = redis.Redis.from_url(REDIS_URL)
    try:
        return list(client.scan_iter(match=f"{PREFIX}*"))
    finally:
        client.close()


def _namespace_snapshot(namespace: str) -> tuple[bytes, bytes, int]:
    keys = _redis_keys(namespace)
    assert len(keys) == 1
    client = redis.Redis.from_url(REDIS_URL)
    try:
        value = client.get(keys[0])
        ttl = client.ttl(keys[0])
    finally:
        client.close()
    assert value is not None
    return keys[0], value, ttl


def _assert_ordinary_ttl() -> None:
    keys = _redis_keys("ordinary")
    assert len(keys) == 1
    # MD5 of "__main__:ordinary:():{}" from published 0.2.2.
    # This must remain a fixed golden; don't rederive it via the fork.
    expected_key = (
        f"{PREFIX}:ordinary:8bab420608af608a3fa1dcf5ee7e2ece".encode()
    )
    assert keys[0] == expected_key, (keys[0], expected_key)
    client = redis.Redis.from_url(REDIS_URL)
    try:
        ttl = client.ttl(keys[0])
    finally:
        client.close()
    assert 0 < ttl <= TTL_SECONDS


def seed_legacy_data() -> None:
    if _prefix_keys():
        raise AssertionError(
            f"Redis prefix {PREFIX!r} already has keys; choose a new test prefix"
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

        unrelated_response = client.get("/unrelated")
        assert unrelated_response.headers["X-FastAPI-Cache"] == "MISS"
        assert client.get("/unrelated").headers["X-FastAPI-Cache"] == "HIT"
        assert unrelated_calls == 1

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
    _assert_ordinary_ttl()
    unrelated_before = _namespace_snapshot("unrelated")
    with TestClient(app) as client:
        cleanup_response = client.post("/migration/cleanup")
        cleanup_counts = cleanup_response.json()
        assert cleanup_counts["private"] >= 1
        assert cleanup_counts["special"] >= 1
        assert not _redis_keys("private")
        assert not _redis_keys("special")
        unrelated_after = _namespace_snapshot("unrelated")
        assert unrelated_after[0] == unrelated_before[0]
        assert unrelated_after[1] == unrelated_before[1]
        assert 0 < unrelated_after[2] <= unrelated_before[2]

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
        # Since published 0.3.1, endpoints explicitly taking Request bypass
        # the default builder even when the request is anonymous.
        # The old harness predated this intentional privacy correction.
        assert "X-FastAPI-Cache" not in anonymous.headers
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
    _assert_ordinary_ttl()
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
    if not REDIS_URL:
        raise SystemExit(
            "REDIS_URL must point to a dedicated Redis 7 test database"
        )
    if os.environ.get("MIGRATION_E2E_CONFIRM_ISOLATED_REDIS") != "YES":
        raise SystemExit(
            "Set MIGRATION_E2E_CONFIRM_ISOLATED_REDIS=YES only for a dedicated test database"
        )
    if not re.fullmatch(
        r"fastapi-cache-migration-e2e-[A-Za-z0-9][A-Za-z0-9_-]{7,63}", PREFIX
    ):
        raise SystemExit(
            "MIGRATION_E2E_PREFIX must start with fastapi-cache-migration-e2e- and use only "
            "letters, digits, hyphens or underscores"
        )
    with redis.Redis.from_url(REDIS_URL) as redis_client:
        redis_version = redis_client.info("server").get("redis_version", "")
    if not redis_version.startswith("7."):
        raise SystemExit(
            f"Redis 7 is required; got {redis_version or 'unknown'}"
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

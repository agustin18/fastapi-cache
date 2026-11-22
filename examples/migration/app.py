# ruff: noqa: S101 - demo assertions are intentional fail-closed checks
"""Same unchanged FastAPI application under two separately installed providers.

This is a deliberately artificial, local-only, InMemory example. It exposes
legacy private cache reuse with *fictional* identities; never use real tokens.
"""

from __future__ import annotations

import importlib.metadata as metadata
import json
import sys
from pathlib import Path

import fastapi_cache
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

app = FastAPI()
calls = {"public": 0, "viewer": 0}


@app.get("/public")
@cache(namespace="public", expire=120)
async def public(response: Response) -> dict[str, int]:
    calls["public"] += 1
    return {"calls": calls["public"]}


@app.get("/viewer")
@cache(namespace="viewer", expire=120)
async def viewer(request: Request) -> dict[str, str]:
    # These are fictitious markers, NOT credentials or an authentication demo.
    calls["viewer"] += 1
    demo_marker = request.headers.get("Authorization")
    return {"viewer": "alice" if demo_marker == "Bearer demo-alice" else "bob"}


def _status(response: Response) -> str | None:
    return response.headers.get("X-FastAPI-Cache")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("legacy", "replacement"):
        raise SystemExit("Usage: app.py legacy|replacement")
    mode = sys.argv[1]
    distribution = (
        "fastapi-cache2" if mode == "legacy" else "fastapi-cache-stable"
    )
    other = (
        "fastapi-cache-stable" if mode == "legacy" else "fastapi-cache2"
    )
    version = "0.2.2" if mode == "legacy" else "0.6.0"
    assert metadata.version(distribution) == version

    try:
        metadata.version(other)
    except metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError("The two providers must never be co-installed")

    module = Path(fastapi_cache.__file__).resolve()
    assert "site-packages" in module.parts, module

    FastAPICache.init(InMemoryBackend(), prefix="migration-demo")
    with TestClient(app) as client:
        first = client.get("/public")
        second = client.get("/public")
        conditional = client.get(
            "/public",
            headers={"If-None-Match": second.headers["ETag"]},
        )
        alice = client.get(
            "/viewer", headers={"Authorization": "Bearer demo-alice"}
        )
        bob = client.get(
            "/viewer", headers={"Authorization": "Bearer demo-bob"}
        )

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == {"calls": 1}
    assert conditional.status_code == 304
    assert conditional.content == b""

    report = {
        "distribution": distribution,
        "version": version,
        "public_statuses": [_status(first), _status(second)],
        "conditional_status": conditional.status_code,
        "viewer_statuses": [_status(alice), _status(bob)],
        "viewer_results": [
            alice.json()["viewer"],
            bob.json()["viewer"],
        ],
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()

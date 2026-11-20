"""Published-distribution-only InMemory migration contract (never import checkout).

Run with python -I in one clean virtual environment per provider.
Outputs a bounded JSON report for a cross-distribution comparison.
"""

from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import sys

import fastapi_cache
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi_cache.key_builder import default_key_builder

EXPECTED_KEY = "migration-parity:ordinary:6c5186afe53d101dea5118bda9aebbcf"
CALLS = {"ordinary": 0, "sync": 0, "variant": 0, "private": 0, "error": 0}

app = FastAPI()


def sample_endpoint(*args, **kwargs):
    """Stable module-level identity for legacy MD5 compatibility golden."""


@app.get("/ordinary")
@cache(namespace="ordinary", expire=120)
async def ordinary(response: Response, number: int = 7):
    CALLS["ordinary"] += 1
    return {"number": number, "calls": CALLS["ordinary"]}


@app.get("/sync")
@cache(namespace="sync", expire=120)
def sync_endpoint(response: Response):
    CALLS["sync"] += 1
    return {"calls": CALLS["sync"]}


@app.get("/variant")
@cache(namespace="variant", expire=120)
async def variant(request: Request):
    CALLS["variant"] += 1
    return {"language": request.headers.get("accept-language", "none")}


@app.get("/private")
@cache(namespace="private", expire=120)
async def private(request: Request):
    CALLS["private"] += 1
    return {"principal": request.headers.get("authorization", "anonymous")}


@app.get("/error")
@cache(namespace="error", expire=120)
async def error(response: Response):
    CALLS["error"] += 1
    response.status_code = 418
    return {"kind": "teapot", "calls": CALLS["error"]}


def status(response):
    return response.headers.get("X-FastAPI-Cache")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("legacy", "stable"):
        raise SystemExit("Usage: published_migration_probe.py legacy|stable")
    mode = sys.argv[1]
    name = "fastapi-cache2" if mode == "legacy" else "fastapi-cache-stable"
    other = "fastapi-cache-stable" if mode == "legacy" else "fastapi-cache2"
    expected = "0.2.2" if mode == "legacy" else "0.4.1"
    assert metadata.version(name) == expected, (name, metadata.version(name))
    try:
        metadata.version(other)
    except metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError("Do not co-install the two fastapi_cache providers")

    module = Path(fastapi_cache.__file__).resolve()
    assert "site-packages" in module.parts, module
    assert not str(module).startswith(str(Path(os.environ["GITHUB_WORKSPACE"]))), module

    key = default_key_builder(
        sample_endpoint,
        "migration-parity:ordinary",
        args=(7,),
        kwargs={"lang": "es"},
    )
    reference = hashlib.md5(
        "__main__:sample_endpoint:(7,):{'lang': 'es'}".encode()
    ).hexdigest()
    assert key == EXPECTED_KEY
    assert key == "migration-parity:ordinary:" + reference

    FastAPICache.init(InMemoryBackend(), prefix="migration-parity")
    try:
        with TestClient(app) as client:
            ordinary_first = client.get("/ordinary")
            ordinary_second = client.get("/ordinary")
            ordinary_conditional = client.get(
                "/ordinary",
                headers={"If-None-Match": ordinary_second.headers["etag"]},
            )
            sync_first = client.get("/sync")
            sync_second = client.get("/sync")
            en = client.get("/variant", headers={"Accept-Language": "en"})
            es = client.get("/variant", headers={"Accept-Language": "es"})
            alice = client.get(
                "/private", headers={"Authorization": "Bearer Alice"}
            )
            bob = client.get(
                "/private", headers={"Authorization": "Bearer Bob"}
            )
            error_first = client.get("/error")
            error_second = client.get("/error")
    finally:
        reset = getattr(FastAPICache, "reset", None)
        if reset is not None:
            reset()

    assert ordinary_first.status_code == ordinary_second.status_code == 200
    assert [status(ordinary_first), status(ordinary_second)] == ["MISS", "HIT"]
    assert ordinary_first.json() == ordinary_second.json() == {
        "number": 7,
        "calls": 1,
    }
    assert CALLS["ordinary"] == 1
    assert ordinary_conditional.status_code == 304
    assert ordinary_conditional.content == b""
    assert status(ordinary_conditional) == "HIT"
    assert ordinary_first.headers["etag"] == ordinary_second.headers["etag"]
    assert [status(sync_first), status(sync_second)] == ["MISS", "HIT"]
    assert sync_first.json() == sync_second.json() == {"calls": 1}
    assert CALLS["sync"] == 1
    assert en.json()["language"] == "en"
    assert alice.json()["principal"] == "Bearer Alice"

    if mode == "legacy":
        # Characterize unsafe published legacy behavior rather than preserve it.
        assert [status(en), status(es)] == ["MISS", "HIT"]
        assert es.json()["language"] == "en"
        assert [status(alice), status(bob)] == ["MISS", "HIT"]
        assert bob.json()["principal"] == "Bearer Alice"
        assert CALLS["variant"] == CALLS["private"] == 1
    else:
        # Published 0.4.1 intentionally fails closed on Request-derived inputs.
        for item in (en, es, alice, bob):
            assert status(item) is None
        assert es.json()["language"] == "es"
        assert bob.json()["principal"] == "Bearer Bob"
        assert CALLS["variant"] == CALLS["private"] == 2
        assert error_first.status_code == error_second.status_code == 418
        assert status(error_first) is None and status(error_second) is None
        assert CALLS["error"] == 2
        etag = ordinary_second.headers["etag"]
        assert etag.startswith('W/"') and etag.endswith('"')

    report = {
        "mode": mode,
        "distribution": name,
        "version": expected,
        "python": sys.version.split()[0],
        "module_location": str(module),
        "golden_default_key": key,
        "ordinary": [status(ordinary_first), status(ordinary_second)],
        "sync": [status(sync_first), status(sync_second)],
        "conditional_304": ordinary_conditional.status_code,
        "etag": ordinary_second.headers["etag"],
        "variant": {
            "statuses": [status(en), status(es)],
            "values": [en.json()["language"], es.json()["language"]],
        },
        "authentication": {
            "statuses": [status(alice), status(bob)],
            "values": [
                alice.json()["principal"],
                bob.json()["principal"],
            ],
        },
        "error": {
            "statuses": [status(error_first), status(error_second)],
            "http_statuses": [error_first.status_code, error_second.status_code],
        },
    }
    path = Path(os.environ["MIGRATION_PARITY_OUTPUT"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

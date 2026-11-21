"""Independent InMemory / HTTP consumer for the exact 0.6.0 candidate artifact.

Run via an installed wheel/sdist from /tmp, not from a repository checkout.
This is not an application-specific production certification.
"""

import asyncio
import importlib.metadata as metadata
import json
from contextvars import ContextVar
from pathlib import Path
from typing import Dict

from fastapi import Depends, FastAPI, Response
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

import fastapi_cache
from fastapi_cache import FastAPICache, default_key_builder
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

GOLDEN = "migration-parity:ordinary:6c5186afe53d101dea5118bda9aebbcf"


def sample_endpoint(value: int, lang: str = "es") -> None:
    return None


def check_bounded_inmemory() -> None:
    """Installed candidate: fixed-capacity LRU and failed resizing are tested."""
    async def verify() -> None:
        backend = InMemoryBackend(max_entries=2)
        await backend.set("a", b"a")
        await backend.set("b", b"b")
        try:
            backend.max_entries = 1  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("max_entries was unexpectedly mutable")
        await backend.set("c", b"c")
        assert backend.max_entries == 2
        assert await backend.get("a") is None
        assert await backend.get("b") == b"b"
        assert await backend.get("c") == b"c"
        assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]

        default = InMemoryBackend()
        assert default.max_entries is None
        await default.set("x", b"x")
        assert await default.get("x") == b"x"

    asyncio.run(verify())


def main() -> None:
    assert metadata.version("fastapi-cache-stable") == "0.6.0"
    assert fastapi_cache.__version__ == "0.6.0"
    check_bounded_inmemory()
    try:
        metadata.version("fastapi-cache2")
    except metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError("Both distributions installed in consumer")
    location = Path(fastapi_cache.__file__).resolve()
    assert "site-packages" in location.parts, location

    key = default_key_builder(
        sample_endpoint, "migration-parity:ordinary",
        args=(7,), kwargs={"lang": "es"},
    )
    # Fixed golden from the original published upstream contract; do not
    # regenerate it with the fork or a cryptographic-compatibility fallback.
    assert key == GOLDEN

    FastAPICache.reset()
    FastAPICache.init(InMemoryBackend(), prefix="candidate-060-inmemory")
    calls = {"ordinary": 0, "variant": 0, "error": 0, "request": 0}
    selected_locale: ContextVar[str] = ContextVar("candidate-locale", default="")
    app = FastAPI()

    async def select_locale(request: Request) -> None:
        selected_locale.set(request.headers.get("Accept-Language", "en"))

    @app.get("/ordinary")
    @cache(expire=60, namespace="ordinary")
    async def ordinary() -> Dict[str, int]:
        calls["ordinary"] += 1
        return {"count": calls["ordinary"]}

    @app.get("/locale", dependencies=[Depends(select_locale)])
    @cache(expire=60, namespace="locale", vary_headers=("Accept-Language",))
    async def locale() -> Response:
        calls["variant"] += 1
        return JSONResponse(
            {"locale": selected_locale.get(), "count": calls["variant"]}
        )

    @app.get("/request")
    @cache(expire=60)
    async def explicit_request(request: Request) -> Dict[str, str]:
        calls["request"] += 1
        return {"tenant": request.headers.get("X-Tenant", "")}

    @app.get("/status")
    @cache(expire=60)
    async def unsafe_status(response: Response) -> Dict[str, int]:
        calls["error"] += 1
        response.status_code = 418
        return {"count": calls["error"]}

    with TestClient(app) as client:
        first = client.get("/ordinary")
        hit = client.get("/ordinary")
        conditional = client.get(
            "/ordinary", headers={"If-None-Match": first.headers["etag"]}
        )
        assert first.json() == hit.json() == {"count": 1}
        assert [r.headers["X-FastAPI-Cache"] for r in
                (first, hit, conditional)] == ["MISS", "HIT", "HIT"]
        assert conditional.status_code == 304
        assert not conditional.content

        en = client.get("/locale", headers={"Accept-Language": "en"})
        en_hit = client.get("/locale", headers={"Accept-Language": "en"})
        en_304 = client.get(
            "/locale",
            headers={
                "Accept-Language": "en",
                "If-None-Match": en.headers["etag"],
            },
        )
        es = client.get("/locale", headers={"Accept-Language": "es"})
        assert en.json() == en_hit.json() == {"locale": "en", "count": 1}
        assert es.json() == {"locale": "es", "count": 2}
        assert [r.headers["X-FastAPI-Cache"] for r in
                (en, en_hit, en_304, es)] == ["MISS", "HIT", "HIT", "MISS"]
        assert en_304.status_code == 304
        assert not en_304.content
        assert all(r.headers["vary"].lower() == "accept-language"
                   for r in (en, en_hit, en_304, es))

        a = client.get("/request", headers={"X-Tenant": "a"})
        b = client.get("/request", headers={"X-Tenant": "b"})
        assert a.json() == {"tenant": "a"}
        assert b.json() == {"tenant": "b"}
        assert all("X-FastAPI-Cache" not in r.headers for r in (a, b))

        failed = client.get("/status")
        failed_again = client.get("/status")
        assert failed.status_code == failed_again.status_code == 418
        assert failed.json() == {"count": 1}
        assert failed_again.json() == {"count": 2}
        assert all("X-FastAPI-Cache" not in r.headers
                   for r in (failed, failed_again))
    FastAPICache.reset()
    print(json.dumps({
        "candidate": "0.6.0",
        "import_path": str(location),
        "default_key": key,
        "ordinary": "MISS/HIT/304",
        "locale_variants": "MISS/HIT/304/MISS",
        "request_explicit": "bypass",
        "error_status": "not_cached",
        "result": "PASS",
    }, sort_keys=True))


if __name__ == "__main__":
    main()

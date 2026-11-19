"""Guard request-dependent cache variants without changing legacy keys."""

import hashlib
from typing import Any, Awaitable, Callable, Dict, Generator, Optional, Tuple

import pytest
from fastapi import FastAPI, Header
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi_cache.key_builder import default_key_builder


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def _variant_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    # Hash (rather than store raw) the response-defining locale value.
    language = request.headers.get("Accept-Language", "") if request else ""
    digest = hashlib.sha256(language.encode("utf-8")).hexdigest()
    return default_key_builder(func, namespace + ":" + digest, args=args, kwargs=kwargs)


def test_explicit_request_bypasses_legacy_shared_default_key() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend)
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/indirect")
    @cache(expire=60)
    async def indirect(request: Request) -> Dict[str, Any]:
        calls["n"] += 1
        return {
            "language": request.headers.get("Accept-Language", ""),
            "n": calls["n"],
        }

    with TestClient(app) as client:
        en = client.get("/indirect", headers={"Accept-Language": "en"})
        es = client.get("/indirect", headers={"Accept-Language": "es"})

    assert en.json() == {"language": "en", "n": 1}
    assert es.json() == {"language": "es", "n": 2}
    assert all("X-FastAPI-Cache" not in r.headers for r in (en, es))
    assert calls["n"] == 2
    assert not backend._store  # pyright: ignore[reportPrivateUsage]


def test_declared_fastapi_header_still_partitions_legacy_keys() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/declared")
    @cache(expire=60)
    async def declared(
        language: str = Header(default="", alias="Accept-Language"),
    ) -> Dict[str, Any]:
        calls["n"] += 1
        return {"language": language, "n": calls["n"]}

    with TestClient(app) as client:
        en = client.get("/declared", headers={"Accept-Language": "en"})
        es = client.get("/declared", headers={"Accept-Language": "es"})
        en_again = client.get("/declared", headers={"Accept-Language": "en"})

    assert [r.headers["X-FastAPI-Cache"] for r in (en, es, en_again)] == [
        "MISS", "MISS", "HIT"
    ]
    assert en.json() == en_again.json() == {"language": "en", "n": 1}
    assert es.json() == {"language": "es", "n": 2}


def test_explicit_request_with_variant_aware_custom_key_caches_safely() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/custom")
    @cache(expire=60, key_builder=_variant_key_builder)
    async def custom(request: Request) -> Dict[str, Any]:
        calls["n"] += 1
        return {
            "language": request.headers.get("Accept-Language", ""),
            "n": calls["n"],
        }

    with TestClient(app) as client:
        en = client.get("/custom", headers={"Accept-Language": "en"})
        es = client.get("/custom", headers={"Accept-Language": "es"})
        en_again = client.get("/custom", headers={"Accept-Language": "en"})

    assert [r.headers["X-FastAPI-Cache"] for r in (en, es, en_again)] == [
        "MISS", "MISS", "HIT"
    ]
    assert en.json() == en_again.json() == {"language": "en", "n": 1}
    assert es.json() == {"language": "es", "n": 2}
    assert calls["n"] == 2


def test_request_state_from_middleware_bypasses_default_key() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()

    @app.middleware("http")
    async def tenant_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.tenant = request.headers.get("X-Tenant", "")
        return await call_next(request)

    @app.get("/tenant")
    @cache(expire=60)
    async def tenant(request: Request) -> Dict[str, str]:
        return {"tenant": request.state.tenant}

    with TestClient(app) as client:
        alpha = client.get("/tenant", headers={"X-Tenant": "alpha"})
        beta = client.get("/tenant", headers={"X-Tenant": "beta"})

    assert alpha.json() == {"tenant": "alpha"}
    assert beta.json() == {"tenant": "beta"}
    assert "X-FastAPI-Cache" not in alpha.headers
    assert "X-FastAPI-Cache" not in beta.headers

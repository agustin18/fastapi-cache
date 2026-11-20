"""RED-first regression contract for explicitly declared HTTP request variants.

These tests run with InMemory; the same key builder and backend protocol are
exercised by the installed-distribution Redis migration checks.
"""

import asyncio
from contextvars import ContextVar
from typing import Any, Dict, Generator, List, Tuple

import pytest
from fastapi import Depends, FastAPI, Header
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi_cache.key_builder import default_key_builder


_module_context: ContextVar[str] = ContextVar("vary-module-region", default="")


async def _module_level_variant() -> Dict[str, str]:
    return {"region": _module_context.get()}


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def test_direct_header_still_uses_unmodified_default_key() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/direct")
    @cache(expire=60)
    async def direct(
        language: str = Header(default="en", alias="Accept-Language"),
    ) -> Dict[str, Any]:
        calls["n"] += 1
        return {"language": language, "n": calls["n"]}

    with TestClient(app) as client:
        en = client.get("/direct", headers={"Accept-Language": "en"})
        es = client.get("/direct", headers={"Accept-Language": "es"})
        again = client.get("/direct", headers={"Accept-Language": "en"})

    assert [r.headers["X-FastAPI-Cache"] for r in (en, es, again)] == [
        "MISS", "MISS", "HIT"
    ]
    assert en.json() == again.json() == {"language": "en", "n": 1}
    assert es.json() == {"language": "es", "n": 2}


def test_hidden_dependency_and_contextvar_are_partitioned_only_when_opted_in() -> None:
    current_language: ContextVar[str] = ContextVar("vary-language", default="unset")
    calls = {"n": 0}
    app = FastAPI()
    FastAPICache.init(InMemoryBackend())

    async def populate(request: Request) -> None:
        current_language.set(request.headers.get("Accept-Language", ""))

    @app.get("/hidden", dependencies=[Depends(populate)])
    @cache(expire=60, vary_headers=[" ACCEPT-LANGUAGE "])
    async def hidden() -> Dict[str, Any]:
        calls["n"] += 1
        return {"language": current_language.get(), "n": calls["n"]}

    with TestClient(app) as client:
        en = client.get("/hidden", headers={"Accept-Language": "en"})
        es = client.get("/hidden", headers={"Accept-Language": "es"})
        again = client.get("/hidden", headers={"Accept-Language": "en"})

    assert [r.headers["X-FastAPI-Cache"] for r in (en, es, again)] == [
        "MISS", "MISS", "HIT"
    ]
    assert en.json() == again.json() == {"language": "en", "n": 1}
    assert es.json() == {"language": "es", "n": 2}
    assert all(r.headers["vary"].lower() == "accept-language" for r in (en, es, again))


def test_request_state_from_middleware_is_partitioned_by_opted_in_tenant() -> None:
    current_tenant: ContextVar[str] = ContextVar("vary-tenant", default="unset")
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="vary-test")
    app = FastAPI()
    calls = {"n": 0}

    @app.middleware("http")
    async def copy_tenant_to_state(request: Request, call_next: Any) -> Response:
        request.state.tenant = request.headers.get("X-Tenant", "")
        return await call_next(request)

    async def capture_state(request: Request) -> None:
        current_tenant.set(request.state.tenant)

    @app.get("/tenant", dependencies=[Depends(capture_state)])
    @cache(expire=60, namespace="tenant", vary_headers=("x-TENANT", "X-Tenant"))
    async def tenant() -> Dict[str, Any]:
        calls["n"] += 1
        return {"tenant": current_tenant.get(), "n": calls["n"]}

    with TestClient(app) as client:
        a = client.get("/tenant", headers={"X-Tenant": "alpha"})
        b = client.get("/tenant", headers={"X-Tenant": "beta"})
        again = client.get("/tenant", headers={"X-Tenant": "alpha"})

    assert [r.headers["X-FastAPI-Cache"] for r in (a, b, again)] == [
        "MISS", "MISS", "HIT"
    ]
    assert a.json() == again.json() == {"tenant": "alpha", "n": 1}
    assert b.json() == {"tenant": "beta", "n": 2}
    assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]
    keys = list(backend._store)  # pyright: ignore[reportPrivateUsage]
    assert all(key.startswith("vary-test:tenant:vary-v1:") for key in keys)
    assert all("alpha" not in key and "beta" not in key for key in keys)


def test_missing_header_empty_header_and_duplicate_values_are_distinct() -> None:
    current: ContextVar[Tuple[str, ...]] = ContextVar("vary-multi", default=())
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    async def resolve(request: Request) -> None:
        current.set(tuple(request.headers.getlist("X-Region")))

    @app.get("/multi", dependencies=[Depends(resolve)])
    @cache(expire=60, vary_headers=("X-Region",))
    async def multi() -> Dict[str, Any]:
        calls["n"] += 1
        return {"region": list(current.get()), "n": calls["n"]}

    with TestClient(app) as client:
        absent = client.get("/multi")
        empty = client.get("/multi", headers={"X-Region": ""})
        repeated = client.get(
            "/multi", headers=[("X-Region", "east"), ("X-Region", "west")]
        )
        reversed_values = client.get(
            "/multi", headers=[("X-Region", "west"), ("X-Region", "east")]
        )
        hit = client.get(
            "/multi", headers=[("x-region", "east"), ("X-Region", "west")]
        )
    assert [r.headers["X-FastAPI-Cache"] for r in
            (absent, empty, repeated, reversed_values, hit)] == [
        "MISS", "MISS", "MISS", "MISS", "HIT"
    ]
    assert absent.json()["region"] == []
    assert empty.json()["region"] == [""]
    assert repeated.json()["region"] == hit.json()["region"] == ["east", "west"]
    assert reversed_values.json()["region"] == ["west", "east"]


def test_declared_vary_is_preserved_on_hit_etag_and_304() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/etag")
    @cache(expire=60, vary_headers=("Accept-Language",))
    async def etag(
        response: Response,
        language: str = Header(default="en", alias="Accept-Language"),
    ) -> Dict[str, Any]:
        calls["n"] += 1
        response.headers["Vary"] = "Accept-Language"
        return {"language": language, "n": calls["n"]}

    with TestClient(app) as client:
        en = client.get("/etag", headers={"Accept-Language": "en"})
        en_again = client.get("/etag", headers={"Accept-Language": "en"})
        conditional = client.get(
            "/etag",
            headers={
                "Accept-Language": "en",
                "If-None-Match": en.headers["etag"],
            },
        )
        es = client.get("/etag", headers={"Accept-Language": "es"})

    assert [r.headers["X-FastAPI-Cache"] for r in
            (en, en_again, conditional, es)] == [
        "MISS", "HIT", "HIT", "MISS"
    ]
    assert conditional.status_code == 304
    assert conditional.content == b""
    assert en.json() == en_again.json() == {"language": "en", "n": 1}
    assert es.json() == {"language": "es", "n": 2}
    assert en.headers["etag"] == en_again.headers["etag"] == conditional.headers["etag"]
    assert all(r.headers["vary"].lower() == "accept-language"
               for r in (en, en_again, conditional, es))


def test_unlisted_vary_header_fails_closed_without_caching() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/unsafe")
    @cache(expire=60, vary_headers=("Accept-Language",))
    async def unsafe(response: Response) -> Dict[str, int]:
        calls["n"] += 1
        response.headers["Vary"] = "X-Unlisted"
        return {"n": calls["n"]}

    with TestClient(app) as client:
        first = client.get("/unsafe")
        second = client.get("/unsafe")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert all("X-FastAPI-Cache" not in r.headers for r in (first, second))


def test_returned_jsonresponse_with_vary_is_not_cached_by_default_coder() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/json")
    @cache(expire=60, vary_headers=("Accept-Language",))
    async def json_result() -> Response:
        calls["n"] += 1
        return JSONResponse(
            {"n": calls["n"]},
            headers={"Vary": "Accept-Language"},
        )

    with TestClient(app) as client:
        first = client.get("/json")
        second = client.get("/json")
    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert all("X-FastAPI-Cache" not in r.headers for r in (first, second))
    assert first.headers["vary"] == second.headers["vary"] == "Accept-Language"


def test_explicit_request_default_builder_still_bypasses_with_vary_headers() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend)
    app = FastAPI()

    @app.get("/request")
    @cache(expire=60, vary_headers=("Accept-Language",))
    async def endpoint(request: Request) -> Dict[str, str]:
        return {"tenant": request.headers.get("X-Tenant", "")}

    with TestClient(app) as client:
        a = client.get("/request", headers={
            "Accept-Language": "en", "X-Tenant": "a"
        })
        b = client.get("/request", headers={
            "Accept-Language": "en", "X-Tenant": "b"
        })

    assert a.json() == {"tenant": "a"}
    assert b.json() == {"tenant": "b"}
    assert all("X-FastAPI-Cache" not in r.headers for r in (a, b))
    assert not backend._store  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize("invalid", [
    "", " ", "bad name", "bad,name", "bad\r\nname", "*",
    "Authorization", "COOKIE", "Proxy-Authorization",
])
def test_invalid_or_sensitive_vary_field_names_are_rejected(invalid: str) -> None:
    with pytest.raises(ValueError, match="vary_headers"):
        cache(vary_headers=(invalid,))


def test_string_instead_of_header_sequence_is_rejected() -> None:
    with pytest.raises(TypeError, match="vary_headers"):
        cache(vary_headers="Accept-Language")  # type: ignore[arg-type]


def test_custom_key_builder_is_not_silently_replaced_by_vary_headers() -> None:
    seen: List[str] = []

    def custom(func: Any, namespace: str = "", *, request: Any = None,
               response: Any = None, args: Any, kwargs: Any) -> str:
        seen.append(namespace)
        return namespace + ":custom-fixed"

    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    language: ContextVar[str] = ContextVar("vary-builder", default="")

    async def resolve(request: Request) -> None:
        language.set(request.headers.get("Accept-Language", ""))

    @app.get("/custom", dependencies=[Depends(resolve)])
    @cache(expire=60, key_builder=custom, vary_headers=("Accept-Language",))
    async def endpoint() -> Dict[str, str]:
        return {"language": language.get()}

    with TestClient(app) as client:
        first = client.get("/custom", headers={"Accept-Language": "en"})
        second = client.get("/custom", headers={"Accept-Language": "es"})
        repeated = client.get("/custom", headers={"Accept-Language": "en"})

    assert [r.headers["X-FastAPI-Cache"] for r in (first, second, repeated)] == [
        "MISS", "MISS", "HIT"
    ]
    assert [first.json(), second.json(), repeated.json()] == [
        {"language": "en"}, {"language": "es"}, {"language": "en"}
    ]
    assert len(seen) == 3


def test_pre_opt_in_legacy_key_cannot_be_read_by_new_variant() -> None:
    """A persisted old shared entry must not feed a newly varied endpoint."""
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="legacy-vary")
    old_key = default_key_builder(
        _module_level_variant, "legacy-vary:tenant", args=(), kwargs={}
    )
    asyncio.run(backend.set(old_key, b'{"region":"stale-from-legacy"}', expire=120))
    app = FastAPI()

    async def select_region(request: Request) -> None:
        _module_context.set(request.headers.get("X-Region", ""))

    app.add_api_route(
        "/module",
        cache(expire=60, namespace="tenant", vary_headers=("X-Region",))(
            _module_level_variant
        ),
        methods=["GET"],
        dependencies=[Depends(select_region)],
    )

    with TestClient(app) as client:
        first = client.get("/module", headers={"X-Region": "north"})
        second = client.get("/module", headers={"X-Region": "north"})

    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert first.json() == second.json() == {"region": "north"}
    assert old_key in backend._store  # pyright: ignore[reportPrivateUsage]
    assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]
    assert asyncio.run(FastAPICache.clear(namespace="tenant")) == 2
    assert not backend._store  # pyright: ignore[reportPrivateUsage]


def test_vary_wildcard_does_not_get_cached_even_if_some_fields_are_declared() -> None:
    FastAPICache.init(InMemoryBackend())
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/wildcard")
    @cache(expire=60, vary_headers=("Accept-Language",))
    async def wildcard(response: Response) -> Dict[str, int]:
        calls["n"] += 1
        response.headers["Vary"] = "*"
        return {"n": calls["n"]}

    with TestClient(app) as client:
        first = client.get("/wildcard")
        second = client.get("/wildcard")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert all("X-FastAPI-Cache" not in r.headers for r in (first, second))


def test_vary_headers_does_not_bypass_authentication_protection() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend)
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/authenticated")
    @cache(expire=60, vary_headers=("Accept-Language",))
    async def authenticated() -> Dict[str, int]:
        calls["n"] += 1
        return {"n": calls["n"]}

    with TestClient(app) as client:
        first = client.get(
            "/authenticated",
            headers={"Authorization": "Bearer alice", "Accept-Language": "en"},
        )
        second = client.get(
            "/authenticated",
            headers={"Authorization": "Bearer bob", "Accept-Language": "en"},
        )
    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert all("X-FastAPI-Cache" not in r.headers for r in (first, second))
    assert not backend._store  # pyright: ignore[reportPrivateUsage]


def test_non_http_invocation_does_not_call_a_variant_key_builder() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend)
    calls = {"n": 0}

    def forbidden_builder(func: Any, namespace: str = "", *,
                          request: Any = None, response: Any = None,
                          args: Any, kwargs: Any) -> str:
        raise AssertionError("no HTTP Request: never create a shared cache key")

    @cache(expire=60, key_builder=forbidden_builder,
           vary_headers=("Accept-Language",))
    async def pure_function() -> Dict[str, int]:
        calls["n"] += 1
        return {"n": calls["n"]}

    assert asyncio.run(pure_function()) == {"n": 1}
    assert asyncio.run(pure_function()) == {"n": 2}
    assert not backend._store  # pyright: ignore[reportPrivateUsage]

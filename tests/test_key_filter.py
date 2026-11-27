import asyncio
import os
import subprocess
import sys
from inspect import Parameter, Signature, signature
from typing import Any, Dict, Generator, List

import httpx
import pytest
from fastapi import (
    Body,
    Cookie,
    Depends,
    FastAPI,
    Header,
    Path,
    Query,
    Security,
)
from fastapi.security import APIKeyHeader
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from typing_extensions import Annotated

from fastapi_cache import (
    CacheConfig,
    CacheHandle,
    FastAPICache,
    default_key_builder,
)
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi_cache.key_filter import filtered_key, validate_exclusions


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    FastAPICache.init(InMemoryBackend(), prefix="filter-tests")
    yield
    FastAPICache.reset()


def service() -> object:
    return object()


def endpoint(value: Any, db: object = Depends(service), limit: int = 5) -> None:  # noqa: B008
    pass


def key(value: Any, db: object = None, **kwargs: Any) -> Any:
    if db is None:
        db = object()
    return filtered_key(endpoint, signature(endpoint), ("db",), "test", None,
                        (value, db), kwargs)


def test_normalization_and_type_separation() -> None:
    first = key("value", object())
    assert first is not None
    assert ":filter-v1:" in first
    assert first == key("value", object(), limit=5)
    assert first == filtered_key(endpoint, signature(endpoint), ("db",), "test",
                                 None, (), {"limit": 5, "db": object(), "value": "value"})
    assert first != key("value", object(), limit=6)
    assert len({key(v) for v in (None, True, 1, 1.0, "1", b"1", 0.0, -0.0)}) == 8


@pytest.mark.parametrize("value", [object(), [], {}, float("nan"), float("inf"), "\ud800"])
def test_unsupported_values_bypass(value: Any) -> None:
    assert key(value) is None


def test_invalid_binding_and_route_identity() -> None:
    assert filtered_key(endpoint, signature(endpoint), ("db",), "test", None, (), {}) is None
    request = Request({"type": "http", "headers": []})
    assert filtered_key(endpoint, signature(endpoint), ("db",), "test", request,
                        (1, object()), {}) is None
    def variadic(*args: Any, **kwargs: Any) -> None:
        pass
    assert filtered_key(variadic, signature(variadic), (), "test", None, (), {}) is None
    def nested(db: object) -> None:
        pass
    assert filtered_key(nested, signature(nested), ("db",), "test", None,
                        (object(),), {}) is None


@pytest.mark.parametrize("names", [("missing",), ("db", "db"), (1,)])
def test_invalid_names(names: Any) -> None:
    with pytest.raises(ValueError, match="Invalid or duplicate"):
        validate_exclusions(signature(endpoint), names, "request", "response")


def test_protected_and_variadic_names() -> None:
    def protected(userId: str, request: Request, response: Response, **kwargs: Any) -> None:
        pass
    for name in ("userId", "request", "response", "kwargs"):
        with pytest.raises(ValueError, match="Cannot exclude"):
            validate_exclusions(signature(protected), (name,), "request", "response")


def test_invalid_options() -> None:
    with pytest.raises(TypeError, match="must be a sequence"):
        cache(exclude_params="db")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="requires the default key builder"):
        cache(exclude_params=("db",), key_builder=lambda *a, **kw: "unsafe")
    with pytest.raises(ValueError, match="Invalid or duplicate"):
        cache(exclude_params=("missing",))(endpoint)  # type: ignore[arg-type]


def test_http_filter_hit_and_auth_bypass() -> None:
    app = FastAPI()
    calls: List[object] = []
    def get_db() -> object:
        return object()

    @app.get("/value")
    @cache(expire=60, exclude_params=("db",))
    async def value(item: int, db: Any = Depends(get_db)) -> Dict[str, int]:  # noqa: B008
        calls.append(db)
        return {"item": item, "calls": len(calls)}

    with TestClient(app) as client:
        a = client.get("/value?item=1")
        b = client.get("/value?item=1")
        c = client.get("/value?item=2")
        assert a.json() == b.json() == {"item": 1, "calls": 1}
        assert b.headers["X-FastAPI-Cache"] == "HIT"
        assert c.json() == {"item": 2, "calls": 2}
        assert client.get("/value?item=1", headers={"Authorization": "synthetic"}).json()["calls"] == 3


def test_http_context_and_custom_builder_bypass() -> None:
    app = FastAPI()
    calls: List[object] = []
    def get_db() -> object:
        return object()

    @app.get("/response")
    @cache(exclude_params=("db",))
    async def response_endpoint(response: Response, db: Any = Depends(get_db)) -> int:  # noqa: B008
        calls.append(db)
        return len(calls)

    @app.get("/custom")
    @cache(exclude_params=("db",))
    async def custom(db: Any = Depends(get_db)) -> int:  # noqa: B008
        calls.append(db)
        return len(calls)

    @app.get("/auth")
    @cache(exclude_params=("db",), cache_authenticated=True)
    async def auth(db: Any = Depends(get_db)) -> int:  # noqa: B008
        calls.append(db)
        return len(calls)

    with TestClient(app) as client:
        for path in ("/response", "/auth"):
            assert client.get(path).json() != client.get(path).json()
        FastAPICache.init(InMemoryBackend(), key_builder=lambda *a, **kw: "custom", force=True)
        assert client.get("/custom").json() != client.get("/custom").json()


def test_unsupported_http_retained_dependency_bypasses() -> None:
    app = FastAPI()
    calls: List[object] = []
    def resource() -> object:
        return object()

    @app.get("/")
    @cache(exclude_params=("db",))
    async def value(db: Any = Depends(resource), other: Any = Depends(resource)) -> int:  # noqa: B008
        calls.append(other)
        return len(calls)

    with TestClient(app) as client:
        assert client.get("/").json() != client.get("/").json()


_DIRECT_CALLS: List[object] = []


async def direct(value: int, db: object = Depends(service)) -> int:  # noqa: B008
    _DIRECT_CALLS.append(db)
    return value


def test_direct_module_level_calls() -> None:
    cached = cache(exclude_params=("db",))(direct)
    _DIRECT_CALLS.clear()
    async def run() -> None:
        resource = object()
        assert await cached(1, resource) == 1
        assert await cached(value=1, db=object()) == 1
        assert _DIRECT_CALLS == [resource]
    asyncio.run(run())


def test_empty_option_preserves_exact_legacy_key() -> None:
    async def verify() -> None:
        backend = FastAPICache.get_backend()
        legacy = cache()(direct)
        empty = cache(exclude_params=())(direct)
        expected = default_key_builder(direct, "filter-tests:", args=(2, "db"), kwargs={})
        assert await legacy(2, "db") == 2
        assert await backend.get(expected) is not None
        assert await empty(2, "db") == 2
        assert await backend.get(expected) is not None
    asyncio.run(verify())


def test_app_scope_vary_and_route_isolation() -> None:
    async def verify() -> None:
        app = FastAPI()
        other = FastAPI()
        backend = InMemoryBackend()
        first = CacheHandle(CacheConfig(backend, scope_id="first"))
        second = CacheHandle(CacheConfig(backend, scope_id="second"))
        calls: List[object] = []

        def db_dependency() -> object:
            return object()

        @app.get("/items")
        @app.get("/other")
        @other.get("/items")
        @cache(scope="app", exclude_params=("db",), vary_headers=("Accept-Language",), expire=60)
        async def items(db: Any = Depends(db_dependency)) -> int:  # noqa: B008
            calls.append(db)
            return len(calls)

        await first.start(app)
        await second.start(other)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                         base_url="http://test") as a, httpx.AsyncClient(
                transport=httpx.ASGITransport(app=other), base_url="http://test"
            ) as b:
                assert (await a.get("/items", headers={"Accept-Language": "en"})).json() == 1
                assert (await a.get("/items", headers={"Accept-Language": "en"})).json() == 1
                assert (await a.get("/items", headers={"Accept-Language": "es"})).json() == 2
                assert (await a.get("/other", headers={"Accept-Language": "en"})).json() == 3
                assert (await b.get("/items", headers={"Accept-Language": "en"})).json() == 4
        finally:
            await second.aclose()
            await first.aclose()
    asyncio.run(verify())


@pytest.mark.parametrize("name", [
    "api_key", "apikey", "access_key", "username", "authz", "payload", "body",
])
def test_identity_and_payload_exclusions_rejected_even_with_depends(name: str) -> None:
    param = Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=Depends(service))
    with pytest.raises(ValueError, match="Cannot exclude"):
        validate_exclusions(Signature([param]), (name,), "request", "response")


@pytest.mark.parametrize("marker", [Parameter.empty, Body(...), Query(...), Path(...), Header(...), Cookie(...)])
def test_request_input_cannot_be_excluded(marker: Any) -> None:
    param = Parameter("data", Parameter.POSITIONAL_OR_KEYWORD, default=marker)
    with pytest.raises(ValueError, match="explicit zero-argument service Depends"):
        validate_exclusions(Signature([param]), ("data",), "request", "response")


def test_original_auditor_reproductions_rejected_at_decoration() -> None:
    async def api(api_key: str) -> str:
        return api_key

    async def body(data: Dict[str, int] = Body(...)) -> Dict[str, int]:  # noqa: B008
        return data

    for func, name in ((api, "api_key"), (body, "data")):
        with pytest.raises(ValueError, match="Cannot exclude|explicit zero-argument"):
            cache(exclude_params=(name,))(func)


def test_dependency_contract_rejects_security_and_request_inputs() -> None:
    def query_input(value: str) -> str:
        return value

    def request_input(request: Request) -> Request:
        return request

    security = APIKeyHeader(name="X-Key")
    for marker in (Depends(), Security(security), Depends(security),
                   Depends(query_input), Depends(request_input), Depends(1)):
        param = Parameter("resource", Parameter.POSITIONAL_OR_KEYWORD, default=marker)
        with pytest.raises(ValueError, match="explicit zero-argument"):
            validate_exclusions(Signature([param]), ("resource",), "request", "response")


def test_annotated_dependency_contract() -> None:
    param = Parameter("db", Parameter.POSITIONAL_OR_KEYWORD,
                      annotation=Annotated[object, Depends(service)])
    validate_exclusions(Signature([param]), ("db",), "request", "response")
    for invalid in (
        param.replace(default=Depends(service)),
        param.replace(annotation=Annotated[object, Query(...)]),
        param.replace(annotation=Annotated[object, Depends(service), "extra"]),
    ):
        with pytest.raises(ValueError, match="explicit zero-argument"):
            validate_exclusions(Signature([invalid]), ("db",), "request", "response")

    app = FastAPI()
    calls: List[object] = []

    @app.get("/annotated")
    @cache(exclude_params=("db",))
    async def view(db: Annotated[object, Depends(service)]) -> int:
        calls.append(db)
        return len(calls)

    with TestClient(app) as client:
        assert client.get("/annotated").json() == 1
        assert client.get("/annotated").headers["X-FastAPI-Cache"] == "HIT"


def test_request_explicit_bypass() -> None:
    app = FastAPI()

    @app.get("/request")
    @cache(exclude_params=("db",))
    async def view(request: Request, db: object = Depends(service)) -> str:  # noqa: B008
        return request.headers["X-Identity"]

    with TestClient(app) as client:
        first = client.get("/request", headers={"X-Identity": "alice"})
        second = client.get("/request", headers={"X-Identity": "bob"})
        assert first.json() == "alice"
        assert second.json() == "bob"
        assert "X-FastAPI-Cache" not in second.headers


def test_host_absent_ambiguous_or_empty_bypasses() -> None:
    for headers in ([], [(b"host", b"")], [(b"host", b"a"), (b"host", b"b")]):
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": headers})
        assert filtered_key(endpoint, signature(endpoint), ("db",), "test", request,
                            (1, object()), {}) is None


def test_no_mutation_and_missing_or_scalar_dependencies_bypass() -> None:
    db = object()
    kwargs = {"db": db, "value": 1}
    before = kwargs.copy()
    assert filtered_key(endpoint, signature(endpoint), ("db",), "test", None, (), kwargs)
    assert kwargs == before
    assert kwargs["db"] is db
    assert filtered_key(endpoint, signature(endpoint), ("db",), "test", None, (1,), {}) is None
    for identity in (None, "alice", 1, True, 1.0, b"alice"):
        assert filtered_key(endpoint, signature(endpoint), ("db",), "test", None,
                            (1, identity), {}) is None


def test_override_bypasses_existing_filtered_entry() -> None:
    app = FastAPI()
    calls: List[object] = []

    @app.get("/override")
    @cache(exclude_params=("db",))
    async def view(db: object = Depends(service)) -> int:  # noqa: B008
        calls.append(db)
        return len(calls)

    with TestClient(app) as client:
        assert client.get("/override").json() == 1
        assert client.get("/override").headers["X-FastAPI-Cache"] == "HIT"
        app.dependency_overrides[service] = service
        assert client.get("/override").json() == 2
        assert client.get("/override").json() == 3


def test_cross_process_hashseed_determinism() -> None:
    script = """
from inspect import signature
from fastapi_cache.key_filter import filtered_key

def endpoint(value, db, limit=5):
    pass
print(filtered_key(endpoint, signature(endpoint), ("db",), "test", None,
                   (), {"value": "hello", "db": object(), "limit": 5}))
"""
    outputs = [
        subprocess.check_output(  # noqa: S603
            [sys.executable, "-c", script],
            env=dict(os.environ, PYTHONHASHSEED=seed), text=True,
        ).strip()
        for seed in ("1", "42", "999")
    ]
    assert len(set(outputs)) == 1
    assert outputs[0].startswith("test:filter-v1:")

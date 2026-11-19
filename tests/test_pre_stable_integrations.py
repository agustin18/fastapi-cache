"""Pre-stable integration contracts and documented legacy key behavior."""

from inspect import signature
from typing import Any, Callable, Dict, Generator, Optional, Tuple, Union

import pytest
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache, default_key_builder
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


class Item(BaseModel):
    id: int
    label: str


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def test_annotated_return_type_survives_decorator_and_openapi() -> None:
    """Upstream #384: no explicit response_model should be necessary."""
    app = FastAPI()
    counters = {"implicit": 0, "explicit": 0}

    @app.get("/implicit")
    @cache(namespace="implicit", expire=60, infer_response_model=True)
    async def implicit() -> Item:
        counters["implicit"] += 1
        return Item(id=1, label="implicit")

    @app.get("/explicit", response_model=Item)
    @cache(namespace="explicit", expire=60)
    async def explicit() -> Item:
        counters["explicit"] += 1
        return Item(id=2, label="explicit")

    assert signature(implicit).return_annotation is Item
    schema = app.openapi()
    for path in ("/implicit", "/explicit"):
        model = schema["paths"][path]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert model["$ref"].endswith("/Item")

    FastAPICache.init(InMemoryBackend(), prefix="openapi")
    with TestClient(app) as client:
        for path, expected_id in (("/implicit", 1), ("/explicit", 2)):
            first = client.get(path)
            second = client.get(path)
            assert first.status_code == second.status_code == 200
            assert first.json() == second.json() == {
                "id": expected_id,
                "label": path.lstrip("/"),
            }
            assert first.headers["X-FastAPI-Cache"] == "MISS"
            assert second.headers["X-FastAPI-Cache"] == "HIT"

    assert counters == {"implicit": 1, "explicit": 1}


def test_unannotated_endpoint_does_not_gain_response_model() -> None:
    app = FastAPI()

    @app.get("/untyped")
    @cache(expire=60)
    async def untyped():
        return {"ok": True}

    assert signature(untyped).return_annotation is signature(
        lambda: None
    ).return_annotation
    FastAPICache.init(InMemoryBackend(), prefix="untyped")
    with TestClient(app) as client:
        assert client.get("/untyped").status_code == 200


class Session:
    """Fresh per-request session; stable_repr is *not* the default."""

    next_id = 0

    def __init__(self) -> None:
        type(self).next_id += 1
        self.identity = type(self).next_id

    def __repr__(self) -> str:
        return f"<Session {self.identity}>"


async def session_dependency() -> Session:
    return Session()


def test_injected_session_causes_inherited_default_key_misses() -> None:
    """Preserve the old key builder; document permanent MISS from DB objects."""
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/items")
    @cache(namespace="session-default", expire=60)
    async def items(
        session: Session = Depends(session_dependency),  # noqa: B008 - FastAPI DI
    ) -> Dict[str, int]:
        calls["n"] += 1
        return {"n": calls["n"]}

    FastAPICache.init(InMemoryBackend(), prefix="session")
    with TestClient(app) as client:
        first = client.get("/items")
        second = client.get("/items")
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "MISS"
    assert calls["n"] == 2


def safe_public_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    """Skip only a volatile DB object, NOT the tenant or request identity."""
    filtered = {key: value for key, value in kwargs.items() if key != "session"}
    return default_key_builder(
        func, namespace, request=request, response=response,
        args=args, kwargs=filtered,
    )


def test_opt_in_custom_key_avoids_misses_without_cross_tenant_reuse() -> None:
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/items")
    @cache(namespace="session-custom", expire=60, key_builder=safe_public_key_builder)
    async def items(
        tenant: str,
        session: Session = Depends(session_dependency),  # noqa: B008 - FastAPI DI
    ) -> Dict[str, Any]:
        calls["n"] += 1
        return {"tenant": tenant, "n": calls["n"]}

    FastAPICache.init(InMemoryBackend(), prefix="session")
    with TestClient(app) as client:
        first = client.get("/items", params={"tenant": "alpha"})
        second = client.get("/items", params={"tenant": "alpha"})
        other = client.get("/items", params={"tenant": "beta"})
        private = client.get(
            "/items", params={"tenant": "alpha"},
            headers={"Authorization": "Bearer session"},
        )

    assert [r.headers.get("X-FastAPI-Cache") for r in (first, second, other)] == [
        "MISS", "HIT", "MISS",
    ]
    assert first.json() == second.json() == {"tenant": "alpha", "n": 1}
    assert other.json() == {"tenant": "beta", "n": 2}
    assert "X-FastAPI-Cache" not in private.headers
    assert calls["n"] == 3
def test_return_model_inference_is_explicit_opt_in() -> None:
    """Preserve original route behavior unless an application chooses inference."""
    app = FastAPI()

    @app.get("/legacy")
    @cache(namespace="legacy")
    async def legacy() -> Item:
        return Item(id=3, label="legacy")

    @app.get("/inferred")
    @cache(namespace="inferred", infer_response_model=True)
    async def inferred() -> Item:
        return Item(id=4, label="inferred")

    responses = app.openapi()["paths"]
    legacy_schema = responses["/legacy"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    inferred_schema = responses["/inferred"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert legacy_schema == {}
    assert inferred_schema["$ref"].endswith("/Item")

    FastAPICache.init(InMemoryBackend(), prefix="opt-in")
    with TestClient(app) as client:
        for path, item_id in (("/legacy", 3), ("/inferred", 4)):
            first = client.get(path)
            second = client.get(path)
            assert first.status_code == second.status_code == 200
            assert first.json() == second.json() == {
                "id": item_id,
                "label": path.lstrip("/"),
            }
            assert first.headers["X-FastAPI-Cache"] == "MISS"
            assert second.headers["X-FastAPI-Cache"] == "HIT"


def test_legacy_union_response_annotation_keeps_route_registration() -> None:
    """FastAPI cannot infer Union[Response, dict] as a response model."""
    app = FastAPI()

    @app.get("/possibly-response")
    @cache(namespace="possibly-response")
    async def possibly_response() -> Union[Response, Dict[str, int]]:
        return {"count": 1}

    assert app.openapi()["paths"]["/possibly-response"]["get"]["responses"][
        "200"
    ]["content"]["application/json"]["schema"] == {}

    FastAPICache.init(InMemoryBackend(), prefix="union")
    with TestClient(app) as client:
        first = client.get("/possibly-response")
        second = client.get("/possibly-response")
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json() == {"count": 1}
        assert first.headers["X-FastAPI-Cache"] == "MISS"
        assert second.headers["X-FastAPI-Cache"] == "HIT"


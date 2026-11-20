"""Regression for generated FastAPI handlers sharing legacy cache identities."""

from typing import Awaitable, Callable, Dict, Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache, JsonCoder, default_key_builder
from fastapi_cache.backends.inmemory import InMemoryBackend, Value
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def _factory(value: str) -> Callable[[], Awaitable[Dict[str, str]]]:
    async def endpoint() -> Dict[str, str]:
        return {"value": value}

    return endpoint


async def module_level_endpoint() -> Dict[str, str]:
    return {"value": "module"}


def test_factory_legacy_key_identity_collides() -> None:
    """Keep the old raw builder contract visible instead of rewriting it."""
    left, right = _factory("A"), _factory("B")
    assert left is not right
    assert left.__module__ == right.__module__
    assert left.__name__ == right.__name__
    assert default_key_builder(left, "factory:", args=(), kwargs={}) == (
        default_key_builder(right, "factory:", args=(), kwargs={})
    )


def test_factory_http_routes_isolate_cache_and_keep_hits() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    app = FastAPI()
    app.add_api_route("/a", cache(expire=60)(_factory("A")), methods=["GET"])
    app.add_api_route("/b", cache(expire=60)(_factory("B")), methods=["GET"])

    with TestClient(app) as client:
        first_a = client.get("/a")
        first_b = client.get("/b")
        second_a = client.get("/a")
        second_b = client.get("/b")

    assert first_a.json() == second_a.json() == {"value": "A"}
    assert first_b.json() == second_b.json() == {"value": "B"}
    assert [first_a.headers["X-FastAPI-Cache"], first_b.headers["X-FastAPI-Cache"]] == [
        "MISS",
        "MISS",
    ]
    assert [second_a.headers["X-FastAPI-Cache"], second_b.headers["X-FastAPI-Cache"]] == [
        "HIT",
        "HIT",
    ]
    # Retain the published namespace prefix so clear(namespace=...) works.
    assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]
    assert all(
        key.startswith("factory::")
        for key in backend._store  # pyright: ignore[reportPrivateUsage]
    )


def test_factory_route_does_not_replay_existing_0_4_0_entry() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    handler = _factory("fresh")
    legacy_key = default_key_builder(handler, "factory:", args=(), kwargs={})
    backend._store[legacy_key] = Value(  # pyright: ignore[reportPrivateUsage]
        JsonCoder.encode({"value": "stale-from-another-route"}), None
    )

    app = FastAPI()
    app.add_api_route("/new", cache(expire=60)(handler), methods=["GET"])

    with TestClient(app) as client:
        first = client.get("/new")
        second = client.get("/new")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == {"value": "fresh"}
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert legacy_key in backend._store  # pyright: ignore[reportPrivateUsage]


def test_module_level_http_endpoint_uses_unchanged_legacy_key() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    legacy_key = default_key_builder(
        module_level_endpoint, "factory:", args=(), kwargs={}
    )
    app = FastAPI()
    app.add_api_route("/ordinary", cache(expire=60)(module_level_endpoint), methods=["GET"])

    with TestClient(app) as client:
        first = client.get("/ordinary")
        second = client.get("/ordinary")

    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert first.json() == second.json() == {"value": "module"}
    assert legacy_key in backend._store  # pyright: ignore[reportPrivateUsage]
    assert len(backend._store) == 1  # pyright: ignore[reportPrivateUsage]

"""Regression for generated FastAPI handlers sharing legacy cache identities."""

import asyncio
from functools import wraps
from typing import Awaitable, Callable, Dict, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache, JsonCoder, default_key_builder
from fastapi_cache.backends.inmemory import InMemoryBackend, Value
from fastapi_cache.decorator import _route_scoped_generated_key, cache


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


@wraps(module_level_endpoint)
async def decorated_module_level_endpoint() -> Dict[str, str]:
    """An explicit wrapper with no freevars still gets a scoped cache key."""
    return {"value": "decorated-module"}




def _wrapped_factory(value: str) -> Callable[[], Awaitable[Dict[str, str]]]:
    @wraps(module_level_endpoint)
    async def endpoint() -> Dict[str, str]:
        return {"value": value}

    return endpoint


def _wrapped_default_factory(
    value: str,
) -> Callable[..., Awaitable[Dict[str, str]]]:
    # Unlike a closure capture, default-bound values have NO co_freevars.
    # wraps copies the module-level template's name/qualname/signature.
    @wraps(module_level_endpoint)
    async def endpoint(value: str = value) -> Dict[str, str]:
        return {"value": value}

    return endpoint


def _mock_request(
    *, host: str = "example.test", method: str = "GET",
    root_path: str = "", path: str = "/a"
) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "root_path": root_path,
            "path": path,
            "headers": [(b"host", host.encode("ascii"))],
        }
    )

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


def test_generated_handler_without_stable_http_path_fails_closed() -> None:
    """An incomplete ASGI scope never reads or writes a legacy shared key."""
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    calls = [0]

    @cache(expire=60)
    async def endpoint() -> Dict[str, int]:
        calls[0] += 1
        return {"n": calls[0]}

    # The request is sufficient for an HTTP method/header check but lacks
    # the route/path needed to derive a non-colliding generated-handler key.
    request = Request({"type": "http", "method": "GET", "headers": []})

    async def run() -> None:
        first = await endpoint(__fastapi_cache_request=request)  # type: ignore[call-arg]
        second = await endpoint(__fastapi_cache_request=request)  # type: ignore[call-arg]
        assert first == {"n": 1}
        assert second == {"n": 2}

    asyncio.run(run())
    assert calls == [2]
    assert not backend._store  # pyright: ignore[reportPrivateUsage]


def test_functools_wraps_factory_routes_keep_separate_cached_results() -> None:
    """functools.wraps masks __name__/__qualname__, not actual closure code."""
    left, right = _wrapped_factory("A"), _wrapped_factory("B")
    assert left.__name__ == right.__name__ == module_level_endpoint.__name__
    assert left.__qualname__ == right.__qualname__ == module_level_endpoint.__qualname__
    assert "<locals>" not in left.__qualname__
    assert left.__closure__ is not None
    assert left.__code__.co_freevars
    assert default_key_builder(left, "factory:", args=(), kwargs={}) == (
        default_key_builder(right, "factory:", args=(), kwargs={})
    )

    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    app = FastAPI()
    app.add_api_route("/a", cache(expire=60)(left), methods=["GET"])
    app.add_api_route("/b", cache(expire=60)(right), methods=["GET"])

    with TestClient(app) as client:
        first_a = client.get("/a")
        first_b = client.get("/b")
        second_a = client.get("/a")
        second_b = client.get("/b")

    assert first_a.json() == second_a.json() == {"value": "A"}
    assert first_b.json() == second_b.json() == {"value": "B"}
    assert first_a.headers["X-FastAPI-Cache"] == "MISS"
    assert first_b.headers["X-FastAPI-Cache"] == "MISS"
    assert second_a.headers["X-FastAPI-Cache"] == "HIT"
    assert second_b.headers["X-FastAPI-Cache"] == "HIT"
    assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]


def test_wrapped_factory_does_not_reuse_poisoned_legacy_entry() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    handler = _wrapped_factory("fresh")
    legacy_key = default_key_builder(handler, "factory:", args=(), kwargs={})
    backend._store[legacy_key] = Value(  # pyright: ignore[reportPrivateUsage]
        JsonCoder.encode({"value": "old-colliding-value"}), None
    )
    app = FastAPI()
    app.add_api_route("/wrapped", cache(expire=60)(handler), methods=["GET"])

    with TestClient(app) as client:
        first = client.get("/wrapped")
        second = client.get("/wrapped")

    assert first.json() == second.json() == {"value": "fresh"}
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert legacy_key in backend._store  # pyright: ignore[reportPrivateUsage]


def test_scoped_generated_key_separates_method_root_path_and_path() -> None:
    handler = _wrapped_factory("A")
    legacy = default_key_builder(handler, "factory:routes", args=(), kwargs={})
    key = _route_scoped_generated_key(
        handler, _mock_request(), legacy, "factory:routes"
    )
    assert key is not None
    for other in (
        _mock_request(method="POST"),
        _mock_request(root_path="/mounted"),
        _mock_request(path="/b"),
        _mock_request(host="other.example.test"),
    ):
        assert _route_scoped_generated_key(
            handler, other, legacy, "factory:routes"
        ) != key
    # The full HTTP decorator bypasses non-GET requests; here we separately
    # exercise the key partition's method component.


def test_host_case_normalization_and_distinct_hosts() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    app = FastAPI()
    app.add_api_route("/host", cache(expire=60)(_wrapped_factory("A")), methods=["GET"])

    with TestClient(app) as client:
        upper = client.get("/host", headers={"Host": "EXAMPLE.TEST"})
        lower = client.get("/host", headers={"Host": "example.test"})
        other = client.get("/host", headers={"Host": "other.example.test"})
        other_again = client.get("/host", headers={"Host": "other.example.test"})

    assert upper.headers["X-FastAPI-Cache"] == "MISS"
    assert lower.headers["X-FastAPI-Cache"] == "HIT"
    assert other.headers["X-FastAPI-Cache"] == "MISS"
    assert other_again.headers["X-FastAPI-Cache"] == "HIT"
    assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]


def test_clear_named_namespace_for_generated_routes() -> None:
    async def run() -> None:
        backend = InMemoryBackend()
        FastAPICache.init(backend, prefix="factory")
        app = FastAPI()
        app.add_api_route(
            "/a", cache(expire=60, namespace="generated")(_wrapped_factory("A")),
            methods=["GET"],
        )
        app.add_api_route(
            "/b", cache(expire=60, namespace="generated")(_wrapped_factory("B")),
            methods=["GET"],
        )
        app.add_api_route(
            "/other", cache(expire=60, namespace="other")(_wrapped_factory("C")),
            methods=["GET"],
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            first_a = await client.get("/a")
            first_b = await client.get("/b")
            first_other = await client.get("/other")
            assert all(
                result.headers["X-FastAPI-Cache"] == "MISS"
                for result in (first_a, first_b, first_other)
            )
            assert await FastAPICache.clear(namespace="generated") == 2
            assert all(
                key.startswith("factory:other:")
                for key in backend._store  # pyright: ignore[reportPrivateUsage]
            )
            second_a = await client.get("/a")
            second_b = await client.get("/b")
            second_other = await client.get("/other")

        assert second_a.headers["X-FastAPI-Cache"] == "MISS"
        assert second_b.headers["X-FastAPI-Cache"] == "MISS"
        assert second_other.headers["X-FastAPI-Cache"] == "HIT"
        assert second_a.json() == {"value": "A"}
        assert second_b.json() == {"value": "B"}
        assert second_other.json() == {"value": "C"}

    asyncio.run(run())


def test_functools_wraps_with_default_bound_factory_routes_do_not_collide() -> None:
    """The generator must not use a stale shared key even without co_freevars."""
    left, right = _wrapped_default_factory("A"), _wrapped_default_factory("B")
    assert left.__name__ == right.__name__ == module_level_endpoint.__name__
    assert left.__qualname__ == right.__qualname__ == module_level_endpoint.__qualname__
    assert "<locals>" not in left.__qualname__
    assert left.__code__.co_freevars == right.__code__.co_freevars == ()
    assert getattr(left, "__wrapped__", None) is module_level_endpoint
    assert getattr(right, "__wrapped__", None) is module_level_endpoint
    assert default_key_builder(left, "factory:", args=(), kwargs={}) == (
        default_key_builder(right, "factory:", args=(), kwargs={})
    )

    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    app = FastAPI()
    app.add_api_route("/a", cache(expire=60)(left), methods=["GET"])
    app.add_api_route("/b", cache(expire=60)(right), methods=["GET"])

    with TestClient(app) as client:
        first_a = client.get("/a")
        first_b = client.get("/b")
        hit_a = client.get("/a")
        hit_b = client.get("/b")

    assert first_a.json() == hit_a.json() == {"value": "A"}
    assert first_b.json() == hit_b.json() == {"value": "B"}
    assert first_a.headers["X-FastAPI-Cache"] == "MISS"
    assert first_b.headers["X-FastAPI-Cache"] == "MISS"
    assert hit_a.headers["X-FastAPI-Cache"] == "HIT"
    assert hit_b.headers["X-FastAPI-Cache"] == "HIT"
    assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]


def test_wrapped_default_handler_does_not_read_shared_old_key() -> None:
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    endpoint = _wrapped_default_factory("fresh")
    old_key = default_key_builder(endpoint, "factory:", args=(), kwargs={})
    backend._store[old_key] = Value(  # pyright: ignore[reportPrivateUsage]
        JsonCoder.encode({"value": "incorrect-cached-response"}), None
    )
    app = FastAPI()
    app.add_api_route("/default", cache(expire=60)(endpoint), methods=["GET"])

    with TestClient(app) as client:
        first = client.get("/default")
        second = client.get("/default")

    assert first.json() == second.json() == {"value": "fresh"}
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert old_key in backend._store  # pyright: ignore[reportPrivateUsage]


def test_module_level_wrapped_handler_rotates_old_key_without_freevars() -> None:
    """Document key rotation for decorators that set __wrapped__ outside factories."""
    endpoint = decorated_module_level_endpoint
    assert endpoint.__code__.co_freevars == ()
    assert endpoint.__qualname__ == module_level_endpoint.__qualname__
    assert endpoint.__wrapped__ is module_level_endpoint

    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="factory")
    old_key = default_key_builder(endpoint, "factory:", args=(), kwargs={})
    backend._store[old_key] = Value(  # pyright: ignore[reportPrivateUsage]
        JsonCoder.encode({"value": "previous-warm-cache"}), None
    )

    app = FastAPI()
    app.add_api_route("/decorated", cache(expire=60)(endpoint), methods=["GET"])

    with TestClient(app) as client:
        first = client.get("/decorated")
        second = client.get("/decorated")

    assert first.json() == second.json() == {"value": "decorated-module"}
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert old_key in backend._store  # pyright: ignore[reportPrivateUsage]
    assert len(backend._store) == 2  # pyright: ignore[reportPrivateUsage]

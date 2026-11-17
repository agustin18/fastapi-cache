import time
from typing import Any, Dict, Generator, List, Tuple

import pendulum
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from examples.in_memory.main import app
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[Any, Any, None]:  # pyright: ignore[reportUnusedFunction]
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def test_datetime() -> None:
    with TestClient(app) as client:
        response = client.get("/datetime")
        assert response.headers.get("X-FastAPI-Cache") == "MISS"
        first = response.json().get("now")
        first_dt = pendulum.parse(first)
        assert isinstance(first_dt, pendulum.DateTime)
        assert abs(pendulum.now().diff(first_dt).in_seconds()) < 5

        response = client.get("/datetime")
        assert response.headers.get("X-FastAPI-Cache") == "HIT"
        assert response.json().get("now") == first

        time.sleep(5)
        response = client.get("/datetime")
        assert response.headers.get("X-FastAPI-Cache") == "MISS"
        second = response.json().get("now")
        assert second != first
        second_dt = pendulum.parse(second)
        assert isinstance(second_dt, pendulum.DateTime)
        assert abs(pendulum.now().diff(second_dt).in_seconds()) < 5


def test_date() -> None:
    """Test path function without request or response arguments."""
    with TestClient(app) as client:
        response = client.get("/date")
        assert response.headers.get("X-FastAPI-Cache") == "MISS"
        assert pendulum.parse(response.json()) == pendulum.today()

        # do it again to test cache
        response = client.get("/date")
        assert response.headers.get("X-FastAPI-Cache") == "HIT"
        assert pendulum.parse(response.json()) == pendulum.today()

        # now test with cache disabled, as that's a separate code path
        FastAPICache._enable = False  # pyright: ignore[reportPrivateUsage]
        response = client.get("/date")
        assert "X-FastAPI-Cache" not in response.headers
        assert pendulum.parse(response.json()) == pendulum.today()
        FastAPICache._enable = True # pyright: ignore[reportPrivateUsage]


def test_inmemory_lifespan_resets_cache_for_repeated_testclient() -> None:
    for _ in range(2):
        with TestClient(app) as client:
            response = client.get("/date")
            assert response.headers["X-FastAPI-Cache"] == "MISS"

        with pytest.raises(AssertionError, match="You must call init first!"):
            FastAPICache.get_backend()


def test_sync() -> None:
    """Ensure that sync function support works."""
    with TestClient(app) as client:
        response = client.get("/sync-me")
        assert response.json() == 42


def test_cache_response_obj() -> None:
    with TestClient(app) as client:
        cache_response = client.get("cache_response_obj")
        assert cache_response.json() == {"a": 1}
        get_cache_response = client.get("cache_response_obj")
        assert get_cache_response.json() == {"a": 1}
        assert get_cache_response.headers.get("cache-control")
        assert get_cache_response.headers.get("etag")


@pytest.mark.parametrize("path", ["/response_annotation", "/json_response_annotation"])
def test_cache_response_annotations(path: str) -> None:
    with TestClient(app) as client:
        first = client.get(path)
        second = client.get(path)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_kwargs() -> None:
    with TestClient(app) as client:
        name = "Jon"
        response = client.get("/kwargs", params={"name": name})
        assert "X-FastAPI-Cache" not in response.headers
        assert response.json() == {"name": name}


def test_method() -> None:
    with TestClient(app) as client:
        response = client.get("/method")
        assert response.json() == 17


def test_pydantic_model() -> None:
    with TestClient(app) as client:
        r1 = client.get("/pydantic_instance")
        assert r1.headers.get("X-FastAPI-Cache") == "MISS"
        r2 = client.get("/pydantic_instance")
        assert r2.headers.get("X-FastAPI-Cache") == "HIT"
        assert r1.json() == r2.json()


def test_non_get() -> None:
    with TestClient(app) as client:
        first = client.put("/uncached_put")
        assert "X-FastAPI-Cache" not in first.headers
        second = client.put("/uncached_put")
        assert "X-FastAPI-Cache" not in second.headers
        assert second.json()["value"] == first.json()["value"] + 1


def test_cache_error_response_obj_is_not_cached() -> None:
    with TestClient(app) as client:
        for status_code in (404, 500):
            first = client.get("/error_response_obj", params={"status_code": status_code})
            second = client.get("/error_response_obj", params={"status_code": status_code})
            assert first.status_code == status_code
            assert second.status_code == status_code
            assert second.json()["n"] == first.json()["n"] + 1


def test_alternate_injected_namespace() -> None:
    with TestClient(app) as client:
        response = client.get("/namespaced_injection")
        assert response.headers.get("X-FastAPI-Cache") == "MISS"
        assert response.json() == {"__fastapi_cache_request": 42, "__fastapi_cache_response": 17}


def _make_request_cache_control_app() -> Tuple[FastAPI, List[int]]:
    calls = [0]
    test_app = FastAPI()

    @test_app.get("/cached")
    @cache(namespace="request-cache-control", expire=60)
    async def cached() -> Dict[str, int]:
        calls[0] += 1
        return {"value": calls[0]}

    FastAPICache.init(InMemoryBackend())
    return test_app, calls


def test_cache_control() -> None:
    test_app, calls = _make_request_cache_control_app()
    with TestClient(test_app) as client:
        response = client.get("/cached")
        assert response.json() == {"value": 1}

        # HIT
        response = client.get("/cached")
        assert response.json() == {"value": 1}

        # no-cache
        response = client.get("/cached", headers={"Cache-Control": "no-cache"})
        assert response.json() == {"value": 2}

        response = client.get("/cached")
        assert response.json() == {"value": 2}

        # no-store
        response = client.get("/cached", headers={"Cache-Control": "no-store"})
        assert response.json() == {"value": 3}

        response = client.get("/cached")
        assert response.json() == {"value": 2}
        assert calls == [3]


@pytest.mark.parametrize(
    "cache_control",
    ["No-Store", "private, NO-STORE", "no-cache, no-store"],
)
def test_request_no_store_directive_bypasses_read_and_write(
    cache_control: str,
) -> None:
    test_app, calls = _make_request_cache_control_app()
    with TestClient(test_app) as client:
        initial = client.get("/cached")
        cached_value = initial.json()["value"]

        uncached = client.get(
            "/cached", headers={"Cache-Control": cache_control}
        )

        assert uncached.json()["value"] == cached_value + 1
        assert "X-FastAPI-Cache" not in uncached.headers

        following = client.get("/cached")
        assert following.headers["X-FastAPI-Cache"] == "HIT"
        assert following.json()["value"] == cached_value
        assert calls == [cached_value + 1]


@pytest.mark.parametrize(
    "cache_control",
    ["No-Cache", "max-age=0, NO-CACHE", "  no-cache  "],
)
def test_request_no_cache_directive_recomputes_and_refreshes(
    cache_control: str,
) -> None:
    test_app, calls = _make_request_cache_control_app()
    with TestClient(test_app) as client:
        initial = client.get("/cached")
        cached_value = initial.json()["value"]

        refreshed = client.get(
            "/cached", headers={"Cache-Control": cache_control}
        )

        assert refreshed.json()["value"] == cached_value + 1
        assert refreshed.headers["X-FastAPI-Cache"] == "MISS"

        following = client.get("/cached")
        assert following.headers["X-FastAPI-Cache"] == "HIT"
        assert following.json()["value"] == cached_value + 1
        assert calls == [cached_value + 1]


def test_request_no_cache_directive_is_recognized_across_header_fields() -> (
    None
):
    test_app, calls = _make_request_cache_control_app()
    with TestClient(test_app) as client:
        initial = client.get("/cached")
        cached_value = initial.json()["value"]

        refreshed = client.get(
            "/cached",
            headers=[
                ("Cache-Control", "max-age=0"),
                ("Cache-Control", "No-Cache"),
            ],
        )

        assert refreshed.json()["value"] == cached_value + 1
        assert refreshed.headers["X-FastAPI-Cache"] == "MISS"
        assert calls == [cached_value + 1]


@pytest.mark.parametrize(
    "cache_control",
    [
        'extension="no-cache, no-store"',
        'extension="escaped \\", no-cache, no-store"',
    ],
)
def test_directive_names_inside_quoted_extensions_are_ignored(
    cache_control: str,
) -> None:
    test_app, calls = _make_request_cache_control_app()
    with TestClient(test_app) as client:
        initial = client.get("/cached")
        cached_value = initial.json()["value"]

        response = client.get(
            "/cached",
            headers={"Cache-Control": cache_control},
        )

    assert response.json()["value"] == cached_value
    assert response.headers["X-FastAPI-Cache"] == "HIT"
    assert calls == [cached_value]

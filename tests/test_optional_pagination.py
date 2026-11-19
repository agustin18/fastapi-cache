"""Optional reproduction of upstream fastapi-pagination issue #557.

Run explicitly with fastapi-pagination==0.13.1. When not installed, this
test is skipped in the ordinary matrix; the pinned CI lane must PASS, including
cache HIT and cross-page key isolation, without silently expected failures.
"""

from typing import Dict, Generator

import pytest
from fastapi import APIRouter, Depends, FastAPI
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def test_fastapi_pagination_upstream_reproduction() -> None:
    pytest.importorskip("fastapi_pagination")
    from fastapi_pagination import Page, Params, add_pagination, paginate
    
    router = APIRouter()

    @router.get("/items")
    @cache(expire=60, namespace="items")
    async def items(
        params: Params = Depends(),  # noqa: B008 - reproduce upstream FastAPI DI
    ) -> Page[Dict[str, int]]:
        return paginate([{"id": n} for n in range(100)], params)

    app = FastAPI()
    app.include_router(router)
    add_pagination(app)
    FastAPICache.init(InMemoryBackend(), prefix="pagination")

    with TestClient(app) as client:
        first = client.get("/items", params={"page": 1, "size": 10})
        hit = client.get("/items", params={"page": 1, "size": 10})
        second_page = client.get("/items", params={"page": 2, "size": 10})

    assert first.status_code == hit.status_code == second_page.status_code == 200
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert hit.headers["X-FastAPI-Cache"] == "HIT"
    assert second_page.headers["X-FastAPI-Cache"] == "MISS"
    assert first.json() == hit.json()
    assert first.json()["total"] == second_page.json()["total"] == 100
    assert [row["id"] for row in first.json()["items"]] == list(range(10))
    assert [row["id"] for row in second_page.json()["items"]] == list(range(10, 20))

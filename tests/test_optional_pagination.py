"""Optional reproduction of upstream fastapi-pagination issue #557.

Run explicitly with fastapi-pagination==0.13.1. When not installed, this
test is skipped by the ordinary library CI matrix. Only the documented
UninitializedConfigurationError is an expected failure; other exceptions fail.
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
    from fastapi_pagination.errors import UninitializedConfigurationError

    router = APIRouter()

    @router.get("/items")
    @cache(expire=60, namespace="items")
    async def items(params: Params = Depends()) -> Page[Dict[str, int]]:
        return paginate([{"id": n} for n in range(100)], params)

    app = FastAPI()
    app.include_router(router)
    add_pagination(app)
    FastAPICache.init(InMemoryBackend(), prefix="pagination")

    try:
        with TestClient(app) as client:
            response = client.get("/items", params={"page": 1, "size": 10})
    except UninitializedConfigurationError:
        pytest.xfail(
            "Upstream #557: fastapi-pagination 0.13.1 dependency-context "
            "integration is not part of the stable compatibility guarantee."
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == 100
    assert len(payload["items"]) == 10

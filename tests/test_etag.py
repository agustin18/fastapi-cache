import hashlib
from typing import Dict, Generator

import pytest
from fastapi import FastAPI
from starlette.responses import Response
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.coder import JsonCoder
from fastapi_cache.decorator import cache

app = FastAPI()


@app.get("/fixed")
@cache(namespace="test", expire=60)
async def fixed(response: Response) -> Dict[str, str]:
    return {"value": "fixed"}


@app.get("/other")
@cache(namespace="test", expire=60)
async def other(response: Response) -> Dict[str, str]:
    return {"value": "other"}


@pytest.fixture(autouse=True)
def _init_cache() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    FastAPICache.init(InMemoryBackend())
    yield
    FastAPICache.reset()


def test_etag_is_stable_quoted_and_content_based() -> None:
    with TestClient(app) as client:
        first = client.get("/fixed")
        second = client.get("/fixed")
        other = client.get("/other")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers["ETag"] == second.headers["ETag"]
    assert first.headers["ETag"].startswith('W/"')
    assert first.headers["ETag"].endswith('"')
    expected = f'W/"{hashlib.sha256(JsonCoder.encode({"value": "fixed"})).hexdigest()}"'
    assert first.headers["ETag"] == expected
    assert other.headers["ETag"] != first.headers["ETag"]


def test_if_none_match_weak_and_strong() -> None:
    with TestClient(app) as client:
        first = client.get("/fixed")
        etag = first.headers["ETag"]
        weak = client.get("/fixed", headers={"If-None-Match": etag})
        strong = client.get("/fixed", headers={"If-None-Match": etag[2:]})
        non_matching = client.get("/fixed", headers={"If-None-Match": 'W/"other"'})

    assert weak.status_code == 304
    assert weak.headers["ETag"] == etag
    assert weak.headers["X-FastAPI-Cache"] == "HIT"
    assert weak.content == b""
    assert strong.status_code == 304
    assert non_matching.status_code == 200
    assert non_matching.headers["X-FastAPI-Cache"] == "HIT"


def test_if_none_match_list_and_star() -> None:
    with TestClient(app) as client:
        first = client.get("/fixed")
        etag = first.headers["ETag"]
        listed = client.get("/fixed", headers={"If-None-Match": f'"other", {etag}'})
        starred = client.get("/fixed", headers={"If-None-Match": "*"})

    assert listed.status_code == 304
    assert starred.status_code == 304


def test_if_none_match_on_miss_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/fixed", headers={"If-None-Match": "*"})

    assert response.status_code == 200
    assert response.headers["X-FastAPI-Cache"] == "MISS"

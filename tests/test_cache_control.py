from typing import Dict, Generator, Optional

import pytest
from fastapi import FastAPI
from starlette.responses import Response
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

app = FastAPI()


@app.get("/no-expire")
@cache(namespace="test")
async def no_expire(response: Response) -> Dict[str, bool]:
    return {"ok": True}


@app.get("/expire-60")
@cache(namespace="test", expire=60)
async def expire_60(response: Response) -> Dict[str, bool]:
    return {"ok": True}


@app.get("/expire-zero")
@cache(namespace="test", expire=0)
async def expire_zero(response: Response) -> Dict[str, bool]:
    return {"ok": True}


@app.get("/expire-negative")
@cache(namespace="test", expire=-1)
async def expire_negative(response: Response) -> Dict[str, bool]:
    return {"ok": True}


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def _init(expire: Optional[int] = None) -> None:
    FastAPICache.init(InMemoryBackend(), expire=expire)


def test_no_expiration_omits_cache_control_on_miss_and_hit() -> None:
    _init()
    with TestClient(app) as client:
        first = client.get("/no-expire")
        assert first.headers["X-FastAPI-Cache"] == "MISS"
        assert "Cache-Control" not in first.headers
        assert "ETag" in first.headers

        second = client.get("/no-expire")
        assert second.headers["X-FastAPI-Cache"] == "HIT"
        assert "Cache-Control" not in second.headers
        assert "ETag" in second.headers


def test_expiring_entry_emits_valid_max_age() -> None:
    _init()
    with TestClient(app) as client:
        first = client.get("/expire-60")
        assert first.headers["X-FastAPI-Cache"] == "MISS"
        assert first.headers["Cache-Control"] == "max-age=60"

        second = client.get("/expire-60")
        assert second.headers["X-FastAPI-Cache"] == "HIT"
        max_age = int(second.headers["Cache-Control"].split("=", 1)[1])
        assert 0 <= max_age <= 60


def test_expire_zero_keeps_legacy_global_fallback() -> None:
    _init(expire=60)
    with TestClient(app) as client:
        response = client.get("/expire-zero")
        assert response.headers["X-FastAPI-Cache"] == "MISS"
        assert response.headers["Cache-Control"] == "max-age=60"


def test_zero_expire_emits_valid_max_age() -> None:
    _init(expire=0)
    with TestClient(app) as client:
        response = client.get("/no-expire")
        assert response.headers["X-FastAPI-Cache"] == "MISS"
        assert response.headers["Cache-Control"] == "max-age=0"


def test_negative_expire_omits_cache_control() -> None:
    _init()
    with TestClient(app) as client:
        response = client.get("/expire-negative")
        assert response.headers["X-FastAPI-Cache"] == "MISS"
        assert "Cache-Control" not in response.headers

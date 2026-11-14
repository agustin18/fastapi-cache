import atexit
import os
import tempfile
from typing import AsyncIterator, Dict, Generator

import pytest
from fastapi import FastAPI
from starlette.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

app = FastAPI()
counters = {
    "streaming": 0,
    "file": 0,
    "redirect": 0,
    "plain": 0,
    "json": 0,
    "user_spec": 0,
}

_fd, _TEMP_FILE = tempfile.mkstemp()
os.write(_fd, b"file-content")
os.close(_fd)
atexit.register(os.unlink, _TEMP_FILE)


@app.get("/streaming")
@cache(namespace="test", expire=60)
async def streaming() -> StreamingResponse:
    counters["streaming"] += 1

    async def gen() -> AsyncIterator[bytes]:
        yield b"chunk"

    return StreamingResponse(gen(), media_type="text/plain")


@app.get("/file")
@cache(namespace="test", expire=60)
async def file_response() -> FileResponse:
    counters["file"] += 1
    return FileResponse(_TEMP_FILE, media_type="text/plain")


@app.get("/redirect")
@cache(namespace="test", expire=60)
async def redirect() -> RedirectResponse:
    counters["redirect"] += 1
    return RedirectResponse("/target", status_code=307)


@app.get("/plain")
@cache(namespace="test", expire=60)
async def plain() -> Response:
    counters["plain"] += 1
    return PlainTextResponse(f"plain-{counters['plain']}")


@app.get("/json")
@cache(namespace="test", expire=60)
async def json_response() -> JSONResponse:
    counters["json"] += 1
    return JSONResponse({"n": counters["json"]})


@app.get("/user-spec-type")
@cache(namespace="test", expire=60)
async def user_spec_type() -> Dict[str, object]:
    counters["user_spec"] += 1
    return {"_spec_type": "datetime", "val": "2020-01-01", "n": counters["user_spec"]}


@pytest.fixture(autouse=True)
def _init_cache() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    for key in counters:
        counters[key] = 0
    FastAPICache.init(InMemoryBackend())
    yield
    FastAPICache.reset()


def test_streaming_response_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/streaming")
        second = client.get("/streaming")

    assert first.status_code == 200
    assert second.status_code == 200
    assert counters["streaming"] == 2
    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers


def test_file_response_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/file")
        second = client.get("/file")

    assert first.content == b"file-content"
    assert second.content == b"file-content"
    assert counters["file"] == 2
    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers


def test_redirect_response_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/redirect", follow_redirects=False)
        second = client.get("/redirect", follow_redirects=False)

    assert first.status_code == 307
    assert second.status_code == 307
    assert first.headers["location"] == "/target"
    assert second.headers["location"] == "/target"
    assert counters["redirect"] == 2
    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers


def test_plain_response_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/plain")
        second = client.get("/plain")

    assert first.text == "plain-1"
    assert second.text == "plain-2"
    assert counters["plain"] == 2
    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers


def test_json_response_is_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/json")
        second = client.get("/json")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 1}
    assert counters["json"] == 1
    assert second.headers["X-FastAPI-Cache"] == "HIT"


def test_user_spec_type_payload_is_preserved() -> None:
    with TestClient(app) as client:
        first = client.get("/user-spec-type")
        second = client.get("/user-spec-type")

    assert first.json() == {"_spec_type": "datetime", "val": "2020-01-01", "n": 1}
    assert second.json() == {"_spec_type": "datetime", "val": "2020-01-01", "n": 1}
    assert counters["user_spec"] == 1
    assert second.headers["X-FastAPI-Cache"] == "HIT"

import atexit
import os
import tempfile
from typing import AsyncIterator, Dict, Generator

import pytest
from fastapi import Depends, FastAPI, Request
from starlette.background import BackgroundTask
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
from fastapi_cache.coder import PickleCoder
from fastapi_cache.decorator import (  # pyright: ignore[reportPrivateUsage]
    _injected_response_cache_bypass,  # pyright: ignore[reportPrivateUsage]
    cache,
)

app = FastAPI()
counters = {
    "streaming": 0,
    "file": 0,
    "redirect": 0,
    "plain": 0,
    "json": 0,
    "json_created": 0,
    "json_cookie": 0,
    "json_no_store": 0,
    "json_private": 0,
    "json_background": 0,
    "pickle_json_created": 0,
    "pickle_cookie": 0,
    "pickle_private": 0,
    "pickle_public": 0,
    "pickle_streaming": 0,
    "pickle_file": 0,
    "pickle_redirect": 0,
    "pickle_plain": 0,
    "injected_cookie": 0,
    "injected_private": 0,
    "injected_status": 0,
    "injected_public": 0,
    "injected_header": 0,
    "injected_dependency": 0,
    "injected_dependency_header": 0,
    "background_runs": 0,
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


@app.get("/json-created")
@cache(namespace="test", expire=60)
async def json_created() -> JSONResponse:
    counters["json_created"] += 1
    return JSONResponse(
        {"created": True},
        status_code=201,
        headers={"X-Operation": "created"},
    )


@app.get("/json-cookie")
@cache(namespace="test", expire=60)
async def json_cookie() -> JSONResponse:
    counters["json_cookie"] += 1
    return JSONResponse({"ok": True}, headers={"Set-Cookie": "session=abc; HttpOnly"})


@app.get("/json-no-store")
@cache(namespace="test", expire=60)
async def json_no_store() -> JSONResponse:
    counters["json_no_store"] += 1
    return JSONResponse({"ok": True}, headers={"Cache-Control": "no-store"})


@app.get("/json-private")
@cache(namespace="test", expire=60)
async def json_private() -> JSONResponse:
    counters["json_private"] += 1
    return JSONResponse({"ok": True}, headers={"Cache-Control": "private, max-age=60"})


def _background() -> None:
    counters["background_runs"] += 1


@app.get("/json-background")
@cache(namespace="test", expire=60)
async def json_background() -> JSONResponse:
    counters["json_background"] += 1
    return JSONResponse({"ok": True}, background=BackgroundTask(_background))


@app.get("/pickle-json-created")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_json_created() -> JSONResponse:
    counters["pickle_json_created"] += 1
    return JSONResponse(
        {"created": True},
        status_code=201,
        headers={"X-Operation": "created"},
    )


@app.get("/pickle-cookie")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_cookie() -> JSONResponse:
    counters["pickle_cookie"] += 1
    return JSONResponse({"ok": True}, headers={"Set-Cookie": "session=abc; HttpOnly"})


@app.get("/pickle-private")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_private() -> JSONResponse:
    counters["pickle_private"] += 1
    return JSONResponse({"ok": True}, headers={"Cache-Control": "private"})


@app.get("/pickle-public")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_public() -> JSONResponse:
    counters["pickle_public"] += 1
    return JSONResponse({"ok": True}, headers={"Cache-Control": "public, max-age=60"})


@app.get("/pickle-streaming")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_streaming() -> StreamingResponse:
    counters["pickle_streaming"] += 1

    async def gen() -> AsyncIterator[bytes]:
        yield b"chunk"

    return StreamingResponse(gen(), media_type="text/plain")


@app.get("/pickle-file")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_file() -> FileResponse:
    counters["pickle_file"] += 1
    return FileResponse(_TEMP_FILE, media_type="text/plain")


@app.get("/pickle-redirect")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_redirect() -> RedirectResponse:
    counters["pickle_redirect"] += 1
    return RedirectResponse("/target", status_code=307)


@app.get("/pickle-plain")
@cache(namespace="test", expire=60, coder=PickleCoder)
async def pickle_plain() -> Response:
    counters["pickle_plain"] += 1
    return PlainTextResponse(f"plain-{counters['pickle_plain']}")


@app.get("/injected-cookie")
@cache(namespace="test", expire=60)
async def injected_cookie(response: Response) -> Dict[str, int]:
    counters["injected_cookie"] += 1
    response.set_cookie("session", "secret")
    return {"n": counters["injected_cookie"]}


@app.get("/injected-private")
@cache(namespace="test", expire=60)
async def injected_private(response: Response) -> Dict[str, int]:
    counters["injected_private"] += 1
    response.headers["Cache-Control"] = "private, no-store"
    return {"n": counters["injected_private"]}


@app.get("/injected-status")
@cache(namespace="test", expire=60)
async def injected_status(response: Response) -> Dict[str, int]:
    counters["injected_status"] += 1
    response.status_code = 201
    return {"n": counters["injected_status"]}


@app.get("/injected-public")
@cache(namespace="test", expire=60)
async def injected_public(response: Response) -> Dict[str, int]:
    counters["injected_public"] += 1
    return {"n": counters["injected_public"]}


@app.get("/injected-header")
@cache(namespace="test", expire=60)
async def injected_header(response: Response) -> Dict[str, int]:
    counters["injected_header"] += 1
    response.headers["X-Request-ID"] = f"request-{counters['injected_header']}"
    return {"n": counters["injected_header"]}


async def _private_dependency(request: Request, response: Response) -> None:
    if request.headers.get("X-Private") == "1":
        response.headers["Cache-Control"] = "private"


@app.get("/injected-dependency")
@cache(namespace="test", expire=60)
async def injected_dependency(
    response: Response,
    _: None = Depends(_private_dependency),
) -> Dict[str, int]:
    counters["injected_dependency"] += 1
    return {"n": counters["injected_dependency"]}


async def _request_id_dependency(request: Request, response: Response) -> None:
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        response.headers["X-Request-ID"] = request_id


@app.get("/injected-dependency-header")
@cache(namespace="test", expire=60)
async def injected_dependency_header(
    response: Response,
    _: None = Depends(_request_id_dependency),
) -> Dict[str, int]:
    counters["injected_dependency_header"] += 1
    return {"n": counters["injected_dependency_header"]}


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


def test_json_response_with_status_and_headers_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/json-created")
        second = client.get("/json-created")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.headers["X-Operation"] == "created"
    assert second.headers["X-Operation"] == "created"
    assert counters["json_created"] == 2


def test_json_response_with_cookie_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/json-cookie")
        client.cookies.clear()
        second = client.get("/json-cookie")

    assert first.headers["set-cookie"] == "session=abc; HttpOnly"
    assert second.headers["set-cookie"] == "session=abc; HttpOnly"
    assert counters["json_cookie"] == 2


def test_json_response_with_no_store_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/json-no-store")
        second = client.get("/json-no-store")

    assert first.headers["Cache-Control"] == "no-store"
    assert second.headers["Cache-Control"] == "no-store"
    assert counters["json_no_store"] == 2


def test_json_response_with_private_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/json-private")
        second = client.get("/json-private")

    assert first.headers["Cache-Control"] == "private, max-age=60"
    assert second.headers["Cache-Control"] == "private, max-age=60"
    assert counters["json_private"] == 2


def test_json_response_with_background_task_is_not_cached() -> None:
    with TestClient(app) as client:
        client.get("/json-background")
        client.get("/json-background")

    assert counters["json_background"] == 2
    assert counters["background_runs"] == 2


def test_pickle_coder_preserves_json_response_metadata() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-json-created")
        second = client.get("/pickle-json-created")

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.headers["X-Operation"] == "created"
    assert counters["pickle_json_created"] == 1


def test_pickle_coder_does_not_cache_cookie_responses() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-cookie")
        client.cookies.clear()
        second = client.get("/pickle-cookie")

    assert first.headers["set-cookie"] == "session=abc; HttpOnly"
    assert second.headers["set-cookie"] == "session=abc; HttpOnly"
    assert counters["pickle_cookie"] == 2


def test_pickle_coder_does_not_cache_private_responses() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-private")
        second = client.get("/pickle-private")

    assert first.headers["Cache-Control"] == "private"
    assert second.headers["Cache-Control"] == "private"
    assert counters["pickle_private"] == 2


def test_pickle_coder_caches_public_responses() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-public")
        second = client.get("/pickle-public")

    assert first.headers["Cache-Control"] == "public, max-age=60"
    assert second.headers["Cache-Control"] == "public, max-age=60"
    assert counters["pickle_public"] == 1


def test_pickle_coder_does_not_cache_streaming_responses() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-streaming")
        second = client.get("/pickle-streaming")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.content == b"chunk"
    assert second.content == b"chunk"
    assert counters["pickle_streaming"] == 2


def test_pickle_coder_does_not_cache_file_responses() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-file")
        second = client.get("/pickle-file")

    assert first.content == b"file-content"
    assert second.content == b"file-content"
    assert counters["pickle_file"] == 2


def test_pickle_coder_caches_redirect_responses() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-redirect", follow_redirects=False)
        second = client.get("/pickle-redirect", follow_redirects=False)

    assert first.status_code == 307
    assert second.status_code == 307
    assert second.headers["location"] == "/target"
    assert counters["pickle_redirect"] == 1


def test_pickle_coder_caches_plain_responses() -> None:
    with TestClient(app) as client:
        first = client.get("/pickle-plain")
        second = client.get("/pickle-plain")

    assert first.text == "plain-1"
    assert second.text == "plain-1"
    assert counters["pickle_plain"] == 1


def test_injected_response_cookie_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/injected-cookie")
        client.cookies.clear()
        second = client.get("/injected-cookie")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert "session=secret" in first.headers["set-cookie"]
    assert "session=secret" in second.headers["set-cookie"]
    assert counters["injected_cookie"] == 2


def test_injected_response_private_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/injected-private")
        second = client.get("/injected-private")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert first.headers["Cache-Control"] == "private, no-store"
    assert second.headers["Cache-Control"] == "private, no-store"
    assert counters["injected_private"] == 2


def test_injected_response_custom_status_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/injected-status")
        second = client.get("/injected-status")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert counters["injected_status"] == 2


def test_injected_response_public_endpoint_is_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/injected-public")
        second = client.get("/injected-public")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 1}
    assert counters["injected_public"] == 1
    assert second.headers["X-FastAPI-Cache"] == "HIT"


def test_injected_response_dependency_metadata_bypasses_cache() -> None:
    with TestClient(app) as client:
        first = client.get("/injected-dependency")
        second = client.get("/injected-dependency", headers={"X-Private": "1"})
        third = client.get("/injected-dependency")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert second.headers["Cache-Control"] == "private"
    assert third.json() == {"n": 1}
    assert counters["injected_dependency"] == 2


def test_injected_response_custom_header_is_not_cached() -> None:
    with TestClient(app) as client:
        first = client.get("/injected-header")
        second = client.get("/injected-header")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert first.headers["X-Request-ID"] == "request-1"
    assert second.headers["X-Request-ID"] == "request-2"
    assert counters["injected_header"] == 2


def test_injected_response_dependency_custom_header_bypasses_cache() -> None:
    with TestClient(app) as client:
        first = client.get("/injected-dependency-header")
        second = client.get(
            "/injected-dependency-header", headers={"X-Request-ID": "req-2"}
        )
        third = client.get("/injected-dependency-header")

    assert first.json() == {"n": 1}
    assert second.json() == {"n": 2}
    assert second.headers["X-Request-ID"] == "req-2"
    assert third.json() == {"n": 1}
    assert counters["injected_dependency_header"] == 2


def test_injected_response_bypass_ignores_content_length() -> None:
    response = Response()
    response.headers["content-length"] = "0"
    assert _injected_response_cache_bypass(response) is False  # pyright: ignore[reportPrivateUsage]

import asyncio
import inspect
from typing import Dict, Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_cache import (
    Backend,
    Coder,
    FastAPICache,
    JsonCoder,
    KeyBuilder,
    default_key_builder,
)
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def test_public_imports() -> None:
    assert FastAPICache is not None
    assert Backend is not None
    assert Coder is not None
    assert JsonCoder is not None
    assert KeyBuilder is not None
    assert callable(default_key_builder)


def test_init_signature() -> None:
    params = inspect.signature(FastAPICache.init).parameters
    assert list(params) == [
        "backend",
        "prefix",
        "expire",
        "coder",
        "key_builder",
        "cache_status_header",
        "enable",
        "cache_authenticated",
        "force",
    ]
    assert params["prefix"].default == ""
    assert params["expire"].default is None
    assert params["coder"].default is JsonCoder
    assert params["key_builder"].default is default_key_builder
    assert params["cache_status_header"].default == "X-FastAPI-Cache"
    assert params["enable"].default is True
    assert params["cache_authenticated"].default is False
    assert params["force"].default is False
    assert params["force"].kind is inspect.Parameter.KEYWORD_ONLY


def test_cache_signature() -> None:
    params = inspect.signature(cache).parameters
    assert list(params) == [
        "expire",
        "coder",
        "key_builder",
        "namespace",
        "injected_dependency_namespace",
        "cache_authenticated",
        "infer_response_model",
        "vary_headers",
    ]
    assert params["expire"].default is None
    assert params["coder"].default is None
    assert params["key_builder"].default is None
    assert params["namespace"].default == ""
    assert params["injected_dependency_namespace"].default == "__fastapi_cache"
    assert params["cache_authenticated"].default is None
    assert params["infer_response_model"].default is False


def test_backend_protocol() -> None:
    for name in ("get_with_ttl", "get", "set", "clear"):
        assert hasattr(Backend, name)
        assert getattr(Backend, name).__isabstractmethod__ is True


def test_default_key_builder_format() -> None:
    def endpoint() -> int:
        return 1

    key = default_key_builder(endpoint, "ns", args=(), kwargs={})
    assert key.startswith("ns:")
    assert len(key.split(":")[-1]) == 32


def test_json_coder_primitives() -> None:
    for value in (1, "x", [1, 2], {"a": 1}):
        assert JsonCoder.decode(JsonCoder.encode(value)) == value


def test_inmemory_roundtrip() -> None:
    backend = InMemoryBackend()

    async def run() -> None:
        await backend.set("compat:roundtrip", b"v", 60)
        assert await backend.get("compat:roundtrip") == b"v"
        assert await backend.clear(key="compat:roundtrip") == 1
        assert await backend.get("compat:roundtrip") is None

    asyncio.run(run())


def test_decorator_success_path() -> None:
    FastAPICache.init(InMemoryBackend(), prefix="compat")
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/value")
    @cache(expire=60)
    async def value() -> Dict[str, int]:  # pyright: ignore[reportUnusedFunction]
        calls["n"] += 1
        return {"n": calls["n"]}

    with TestClient(app) as client:
        first = client.get("/value")
        second = client.get("/value")

    assert first.status_code == 200
    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert first.json() == second.json() == {"n": 1}
    assert calls["n"] == 1

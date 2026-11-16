import inspect
from typing import Dict, Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.coder import PickleCoder
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def _build_app() -> FastAPI:
    app = FastAPI()
    counters = {"n": 0}

    @app.get("/value")
    @cache(namespace="reinit", expire=60)
    async def value() -> Dict[str, int]:
        counters["n"] += 1
        return {"n": counters["n"]}

    return app


def _build_global_config_app() -> FastAPI:
    """Endpoints that inherit coder and expire from the global configuration."""
    app = FastAPI()
    counters = {"n": 0}

    @app.get("/value")
    @cache(namespace="reinit")
    async def value() -> Dict[str, int]:
        counters["n"] += 1
        return {"n": counters["n"]}

    return app


def test_second_init_without_force_raises() -> None:
    FastAPICache.init(InMemoryBackend(), prefix="first")

    with pytest.raises(RuntimeError, match="already called"):
        FastAPICache.init(InMemoryBackend(), prefix="second")

    assert FastAPICache.get_prefix() == "first"


def test_second_init_error_mentions_reset_and_force() -> None:
    FastAPICache.init(InMemoryBackend())

    with pytest.raises(RuntimeError) as excinfo:
        FastAPICache.init(InMemoryBackend())

    message = str(excinfo.value)
    assert "FastAPICache.reset()" in message
    assert "force=True" in message


def test_second_init_with_force_applies_new_prefix() -> None:
    FastAPICache.init(InMemoryBackend(), prefix="first")
    FastAPICache.init(InMemoryBackend(), prefix="second", force=True)

    assert FastAPICache.get_prefix() == "second"


def test_second_init_with_force_applies_new_coder() -> None:
    FastAPICache.init(InMemoryBackend(), coder=PickleCoder)
    FastAPICache.init(InMemoryBackend(), force=True)

    assert FastAPICache.get_coder() is not PickleCoder


def test_second_init_with_force_applies_new_backend() -> None:
    first = InMemoryBackend()
    second = InMemoryBackend()
    FastAPICache.init(first)
    FastAPICache.init(second, force=True)

    assert FastAPICache.get_backend() is second


def test_second_init_with_force_applies_new_expire_and_status_header() -> None:
    FastAPICache.init(
        InMemoryBackend(), expire=10, cache_status_header="X-First"
    )
    FastAPICache.init(
        InMemoryBackend(),
        expire=20,
        cache_status_header="X-Second",
        force=True,
    )

    assert FastAPICache.get_expire() == 20
    assert FastAPICache.get_cache_status_header() == "X-Second"


def test_second_init_with_force_applies_new_key_builder() -> None:
    def first_builder(*args: object, **kwargs: object) -> str:
        return "first"

    def second_builder(*args: object, **kwargs: object) -> str:
        return "second"

    FastAPICache.init(InMemoryBackend(), key_builder=first_builder)
    FastAPICache.init(InMemoryBackend(), key_builder=second_builder, force=True)

    assert FastAPICache.get_key_builder() is second_builder


def test_second_init_with_force_applies_enable_and_cache_authenticated() -> (
    None
):
    FastAPICache.init(InMemoryBackend(), enable=False, cache_authenticated=True)
    FastAPICache.init(
        InMemoryBackend(),
        enable=True,
        cache_authenticated=False,
        force=True,
    )

    assert FastAPICache.get_enable() is True
    assert FastAPICache.get_cache_authenticated() is False


def test_reinit_with_force_uses_new_backend_for_caching() -> None:
    app = _build_app()
    first = InMemoryBackend()
    second = InMemoryBackend()

    FastAPICache.init(first, prefix="first")
    FastAPICache.init(second, prefix="second", force=True)

    with TestClient(app) as client:
        assert client.get("/value").headers["X-FastAPI-Cache"] == "MISS"
        assert client.get("/value").headers["X-FastAPI-Cache"] == "HIT"

    assert not first._store, list(first._store)
    assert len(second._store) == 1, list(second._store)
    assert all(key.startswith("second:") for key in second._store), list(
        second._store
    )


def test_reinit_with_force_uses_new_coder_for_caching() -> None:
    app = _build_app()
    backend = InMemoryBackend()

    FastAPICache.init(backend, coder=PickleCoder)
    FastAPICache.init(backend, force=True)

    with TestClient(app) as client:
        assert client.get("/value").headers["X-FastAPI-Cache"] == "MISS"
        assert client.get("/value").headers["X-FastAPI-Cache"] == "HIT"

    stored = next(iter(backend._store.values()))  # pyright: ignore[reportPrivateUsage]
    assert stored.data.startswith(b"{"), stored.data[:20]


def test_reset_then_init_applies_new_configuration() -> None:
    FastAPICache.init(InMemoryBackend(), prefix="first")
    FastAPICache.reset()
    FastAPICache.init(InMemoryBackend(), prefix="second")

    assert FastAPICache.get_prefix() == "second"


def test_init_after_reset_does_not_require_force() -> None:
    FastAPICache.init(InMemoryBackend())
    FastAPICache.reset()
    FastAPICache.init(InMemoryBackend())


def test_force_reinit_applies_new_expire_to_already_called_endpoint() -> None:
    app = _build_global_config_app()
    backend = InMemoryBackend()

    FastAPICache.init(backend, expire=10)
    with TestClient(app) as client:
        first = client.get("/value")
        assert first.headers["Cache-Control"] == "max-age=10", dict(
            first.headers
        )

        FastAPICache.init(InMemoryBackend(), expire=60, force=True)

        second = client.get("/value")
        assert second.headers["Cache-Control"] == "max-age=60", dict(
            second.headers
        )


def test_force_reinit_applies_new_coder_to_already_called_endpoint() -> None:
    app = _build_global_config_app()
    pickle_backend = InMemoryBackend()

    FastAPICache.init(pickle_backend, coder=PickleCoder)
    with TestClient(app) as client:
        assert client.get("/value").headers["X-FastAPI-Cache"] == "MISS"

    json_backend = InMemoryBackend()
    FastAPICache.init(json_backend, force=True)

    with TestClient(app) as client:
        assert client.get("/value").headers["X-FastAPI-Cache"] == "MISS"
        assert client.get("/value").headers["X-FastAPI-Cache"] == "HIT"

    stored = next(iter(json_backend._store.values()))  # pyright: ignore[reportPrivateUsage]
    assert stored.data.startswith(b"{"), stored.data[:20]


def test_reusing_a_namespace_across_coders_needs_a_flush() -> None:
    """Documented risk: pickle entries are unreadable by JsonCoder."""
    app = _build_global_config_app()
    backend = InMemoryBackend()

    FastAPICache.init(backend, coder=PickleCoder)
    with TestClient(app) as client:
        assert client.get("/value").headers["X-FastAPI-Cache"] == "MISS"

    FastAPICache.init(backend, force=True)

    with TestClient(app) as client:
        with pytest.raises(UnicodeDecodeError):
            client.get("/value")


def test_reset_then_init_applies_new_expire_to_already_called_endpoint() -> (
    None
):
    app = _build_global_config_app()

    FastAPICache.init(InMemoryBackend(), expire=10)
    with TestClient(app) as client:
        first = client.get("/value")
        assert first.headers["Cache-Control"] == "max-age=10", dict(
            first.headers
        )

        FastAPICache.reset()
        FastAPICache.init(InMemoryBackend(), expire=45)

        second = client.get("/value")
        assert second.headers["Cache-Control"] == "max-age=45", dict(
            second.headers
        )


def test_reset_then_init_applies_new_coder_to_already_called_endpoint() -> None:
    app = _build_global_config_app()
    pickle_backend = InMemoryBackend()

    FastAPICache.init(pickle_backend, coder=PickleCoder)
    with TestClient(app) as client:
        assert client.get("/value").headers["X-FastAPI-Cache"] == "MISS"

    json_backend = InMemoryBackend()
    FastAPICache.reset()
    FastAPICache.init(json_backend)

    with TestClient(app) as client:
        assert client.get("/value").headers["X-FastAPI-Cache"] == "MISS"
        assert client.get("/value").headers["X-FastAPI-Cache"] == "HIT"

    stored = next(iter(json_backend._store.values()))  # pyright: ignore[reportPrivateUsage]
    assert stored.data.startswith(b"{"), stored.data[:20]


def test_endpoint_level_expire_still_wins_after_force_reinit() -> None:
    app = FastAPI()
    counters = {"n": 0}

    @app.get("/pinned")
    @cache(namespace="reinit", expire=7)
    async def pinned() -> Dict[str, int]:
        counters["n"] += 1
        return {"n": counters["n"]}

    FastAPICache.init(InMemoryBackend(), expire=10)
    with TestClient(app) as client:
        first = client.get("/pinned")
        assert first.headers["Cache-Control"] == "max-age=7", dict(
            first.headers
        )

        FastAPICache.init(InMemoryBackend(), expire=60, force=True)

        second = client.get("/pinned")
        assert second.headers["Cache-Control"] == "max-age=7", dict(
            second.headers
        )


def test_force_is_keyword_only() -> None:
    param = inspect.signature(FastAPICache.init).parameters["force"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY

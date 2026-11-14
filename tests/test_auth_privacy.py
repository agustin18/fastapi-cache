import asyncio
import hashlib
import logging
import time
from typing import Any, Callable, Dict, Generator, Optional, Tuple

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from fastapi_cache import (
    FastAPICache,
    JsonCoder,
    KeyBuilder,
    default_key_builder,
)
from fastapi_cache.backends.inmemory import InMemoryBackend, Value
from fastapi_cache.decorator import cache


def _clear_store() -> None:
    InMemoryBackend._store.clear()  # pyright: ignore[reportPrivateUsage]


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    FastAPICache.reset()
    _clear_store()
    yield
    FastAPICache.reset()
    _clear_store()


def init_cache(
    cache_authenticated: bool = False,
    key_builder: KeyBuilder = default_key_builder,
) -> None:
    FastAPICache.init(
        InMemoryBackend(),
        prefix="auth-test",
        cache_authenticated=cache_authenticated,
        key_builder=key_builder,
    )


def auth_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    identity = ""
    if request is not None:
        identity = "|".join(
            [
                request.headers.get("Authorization", ""),
                request.headers.get("Cookie", ""),
            ]
        )
    digest = hashlib.sha256(identity.encode()).hexdigest()
    return f"{namespace}:{func.__module__}:{func.__name__}:{digest}:{args}:{kwargs}"


def build_app(
    cache_authenticated: Optional[bool] = None,
    key_builder: Optional[KeyBuilder] = None,
) -> Tuple[FastAPI, Dict[str, int], Any]:
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/me")
    @cache(
        expire=60,
        cache_authenticated=cache_authenticated,
        key_builder=key_builder,
    )
    async def me(request: Request) -> Dict[str, Any]:
        calls["n"] += 1
        return {
            "authorization": request.headers.get("Authorization"),
            "cookie": request.headers.get("Cookie"),
            "n": calls["n"],
        }

    return app, calls, me


def build_put_app(
    cache_authenticated: Optional[bool] = None,
    key_builder: Optional[KeyBuilder] = None,
) -> Tuple[FastAPI, Dict[str, int]]:
    app = FastAPI()
    calls = {"n": 0}

    @app.put("/me")
    @cache(
        expire=60,
        cache_authenticated=cache_authenticated,
        key_builder=key_builder,
    )
    async def me(request: Request) -> Dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        calls["n"] += 1
        return {
            "authorization": request.headers.get("Authorization"),
            "n": calls["n"],
        }

    return app, calls


class SpyBackend(InMemoryBackend):
    def __init__(self) -> None:
        self.get_with_ttl_calls = 0
        self.set_calls = 0

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        self.get_with_ttl_calls += 1
        return await super().get_with_ttl(key)

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        self.set_calls += 1
        await super().set(key, value, expire)


class FailingBackend(InMemoryBackend):
    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        raise RuntimeError(f"get failed for key {key}")

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        raise RuntimeError(f"set failed for key {key}")


def test_backend_errors_do_not_log_cache_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    backend = FailingBackend()
    FastAPICache.init(backend, prefix="auth-test")
    identity_key = "identity-bearing-cache-key"

    def secret_key_builder(
        func: Callable[..., Any],
        namespace: str = "",
        *,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> str:
        return identity_key

    app, calls, _ = build_app(key_builder=secret_key_builder)

    with caplog.at_level(logging.WARNING):
        with TestClient(app) as client:
            response = client.get("/me")

    assert response.status_code == 200
    assert calls["n"] == 1
    assert identity_key not in caplog.text
    assert "Error retrieving cache entry" in caplog.text
    assert "Error setting cache entry" in caplog.text


def test_authorization_bypasses_by_default() -> None:
    init_cache()
    app, calls, _ = build_app()

    with TestClient(app) as client:
        alice = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob = client.get("/me", headers={"Authorization": "Bearer bob"})
        alice_again = client.get("/me", headers={"Authorization": "Bearer alice"})

    assert alice.json()["authorization"] == "Bearer alice"
    assert bob.json()["authorization"] == "Bearer bob"
    assert alice_again.json()["authorization"] == "Bearer alice"
    assert calls["n"] == 3
    for response in (alice, bob, alice_again):
        assert "X-FastAPI-Cache" not in response.headers


def test_cookie_bypasses_by_default() -> None:
    init_cache()
    app, calls, _ = build_app()

    with TestClient(app) as client:
        alice = client.get("/me", headers={"Cookie": "session=alice"})
        bob = client.get("/me", headers={"Cookie": "session=bob"})
        alice_again = client.get("/me", headers={"Cookie": "session=alice"})

    assert alice.json()["cookie"] == "session=alice"
    assert bob.json()["cookie"] == "session=bob"
    assert alice_again.json()["cookie"] == "session=alice"
    assert calls["n"] == 3
    for response in (alice, bob, alice_again):
        assert "X-FastAPI-Cache" not in response.headers


def test_public_endpoint_still_caches() -> None:
    init_cache()
    app, calls, _ = build_app()

    with TestClient(app) as client:
        first = client.get("/me")
        second = client.get("/me")

    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert first.json() == second.json()
    assert calls["n"] == 1


def test_opt_in_with_safe_key_builder() -> None:
    init_cache()
    app, calls, _ = build_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        alice = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob = client.get("/me", headers={"Authorization": "Bearer bob"})
        alice_again = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob_again = client.get("/me", headers={"Authorization": "Bearer bob"})

    assert alice.headers["X-FastAPI-Cache"] == "MISS"
    assert bob.headers["X-FastAPI-Cache"] == "MISS"
    assert alice_again.headers["X-FastAPI-Cache"] == "HIT"
    assert bob_again.headers["X-FastAPI-Cache"] == "HIT"
    assert alice_again.json() == alice.json()
    assert bob_again.json() == bob.json()
    assert alice.json()["n"] == 1
    assert bob.json()["n"] == 2
    assert calls["n"] == 2


def test_opt_in_public_request_still_caches() -> None:
    init_cache()
    app, calls, _ = build_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        first = client.get("/me")
        second = client.get("/me")

    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert first.json() == second.json()
    assert calls["n"] == 1


def test_global_opt_in() -> None:
    init_cache(cache_authenticated=True, key_builder=auth_key_builder)
    app, calls, _ = build_app()

    with TestClient(app) as client:
        alice = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob = client.get("/me", headers={"Authorization": "Bearer bob"})
        alice_again = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob_again = client.get("/me", headers={"Authorization": "Bearer bob"})

    assert alice.headers["X-FastAPI-Cache"] == "MISS"
    assert bob.headers["X-FastAPI-Cache"] == "MISS"
    assert alice_again.headers["X-FastAPI-Cache"] == "HIT"
    assert bob_again.headers["X-FastAPI-Cache"] == "HIT"
    assert alice_again.json() == alice.json()
    assert bob_again.json() == bob.json()
    assert calls["n"] == 2


def test_decorator_override_enables_auth_cache() -> None:
    init_cache()
    app, calls, _ = build_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        alice = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob = client.get("/me", headers={"Authorization": "Bearer bob"})
        alice_again = client.get("/me", headers={"Authorization": "Bearer alice"})

    assert alice.headers["X-FastAPI-Cache"] == "MISS"
    assert bob.headers["X-FastAPI-Cache"] == "MISS"
    assert alice_again.headers["X-FastAPI-Cache"] == "HIT"
    assert alice_again.json() == alice.json()
    assert calls["n"] == 2


def test_decorator_override_disables_auth_cache() -> None:
    init_cache(cache_authenticated=True)
    app, calls, _ = build_app(cache_authenticated=False)

    with TestClient(app) as client:
        first = client.get("/me", headers={"Authorization": "Bearer alice"})
        second = client.get("/me", headers={"Authorization": "Bearer alice"})

    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers
    assert calls["n"] == 2


def test_no_store_still_bypasses() -> None:
    init_cache()
    app, calls, _ = build_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        first = client.get(
            "/me",
            headers={
                "Authorization": "Bearer alice",
                "Cache-Control": "no-store",
            },
        )
        second = client.get(
            "/me",
            headers={
                "Authorization": "Bearer alice",
                "Cache-Control": "no-store",
            },
        )

    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers
    assert calls["n"] == 2


def test_non_get_still_bypasses() -> None:
    init_cache()
    app, calls = build_put_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        first = client.put("/me", headers={"Authorization": "Bearer alice"})
        second = client.put("/me", headers={"Authorization": "Bearer alice"})

    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers
    assert calls["n"] == 2


def test_bypass_never_accesses_backend() -> None:
    backend = SpyBackend()
    FastAPICache.init(backend, prefix="auth-test")
    app, calls, _ = build_app()

    with TestClient(app) as client:
        authenticated = client.get(
            "/me",
            headers={"Authorization": "Bearer alice"},
        )
        assert backend.get_with_ttl_calls == 0
        assert backend.set_calls == 0

        public = client.get("/me")
        assert backend.get_with_ttl_calls == 1
        assert backend.set_calls == 1

    assert "X-FastAPI-Cache" not in authenticated.headers
    assert public.headers["X-FastAPI-Cache"] == "MISS"
    assert calls["n"] == 2


def test_authenticated_request_ignores_existing_public_entry() -> None:
    init_cache()
    app, calls, _ = build_app()

    with TestClient(app) as client:
        public = client.get("/me")
        assert public.headers["X-FastAPI-Cache"] == "MISS"
        authenticated = client.get(
            "/me",
            headers={"Authorization": "Bearer alice"},
        )

    assert public.json()["authorization"] is None
    assert authenticated.json()["authorization"] == "Bearer alice"
    assert authenticated.json()["n"] == 2
    assert "X-FastAPI-Cache" not in authenticated.headers
    assert calls["n"] == 2


def test_custom_key_builder_without_opt_in_still_bypasses() -> None:
    init_cache()
    app, calls, _ = build_app(key_builder=auth_key_builder)

    with TestClient(app) as client:
        alice = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob = client.get("/me", headers={"Authorization": "Bearer bob"})
        public_first = client.get("/me")
        public_second = client.get("/me")

    assert "X-FastAPI-Cache" not in alice.headers
    assert "X-FastAPI-Cache" not in bob.headers
    assert public_first.headers["X-FastAPI-Cache"] == "MISS"
    assert public_second.headers["X-FastAPI-Cache"] == "HIT"
    assert calls["n"] == 3


def test_opt_in_rejects_default_key_builder() -> None:
    backend = SpyBackend()
    FastAPICache.init(backend, prefix="auth-test")
    app, calls, _ = build_app(cache_authenticated=True)

    with TestClient(app) as client:
        with pytest.raises(ValueError, match="identity-aware key_builder"):
            client.get("/me", headers={"Authorization": "Bearer alice"})

    assert backend.get_with_ttl_calls == 0
    assert backend.set_calls == 0
    assert calls["n"] == 0


def test_global_opt_in_rejects_default_key_builder() -> None:
    backend = SpyBackend()
    FastAPICache.init(
        backend,
        prefix="auth-test",
        cache_authenticated=True,
    )
    app, calls, _ = build_app()

    with TestClient(app) as client:
        with pytest.raises(ValueError, match="identity-aware key_builder"):
            client.get("/me", headers={"Authorization": "Bearer alice"})

    assert backend.get_with_ttl_calls == 0
    assert backend.set_calls == 0
    assert calls["n"] == 0


def test_global_opt_in_with_decorator_safe_builder() -> None:
    init_cache(cache_authenticated=True)
    app, calls, _ = build_app(key_builder=auth_key_builder)

    with TestClient(app) as client:
        alice = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob = client.get("/me", headers={"Authorization": "Bearer bob"})
        alice_again = client.get("/me", headers={"Authorization": "Bearer alice"})
        bob_again = client.get("/me", headers={"Authorization": "Bearer bob"})

    assert alice.headers["X-FastAPI-Cache"] == "MISS"
    assert bob.headers["X-FastAPI-Cache"] == "MISS"
    assert alice_again.headers["X-FastAPI-Cache"] == "HIT"
    assert bob_again.headers["X-FastAPI-Cache"] == "HIT"
    assert alice_again.json() == alice.json()
    assert bob_again.json() == bob.json()
    assert calls["n"] == 2


def test_empty_auth_headers() -> None:
    init_cache()
    app, calls, _ = build_app()

    with TestClient(app) as client:
        first = client.get(
            "/me",
            headers={"Authorization": "", "Cookie": ""},
        )
        second = client.get(
            "/me",
            headers={"Authorization": "", "Cookie": ""},
        )

    assert first.headers["X-FastAPI-Cache"] == "MISS"
    assert second.headers["X-FastAPI-Cache"] == "HIT"
    assert calls["n"] == 1


def test_cookie_and_authorization_together() -> None:
    init_cache()
    app, calls, _ = build_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        alice = client.get(
            "/me",
            headers={
                "Authorization": "Bearer alice",
                "Cookie": "session=alice",
            },
        )
        bob = client.get(
            "/me",
            headers={
                "Authorization": "Bearer bob",
                "Cookie": "session=bob",
            },
        )
        alice_again = client.get(
            "/me",
            headers={
                "Authorization": "Bearer alice",
                "Cookie": "session=alice",
            },
        )
        bob_again = client.get(
            "/me",
            headers={
                "Authorization": "Bearer bob",
                "Cookie": "session=bob",
            },
        )

    assert alice.headers["X-FastAPI-Cache"] == "MISS"
    assert bob.headers["X-FastAPI-Cache"] == "MISS"
    assert alice_again.headers["X-FastAPI-Cache"] == "HIT"
    assert bob_again.headers["X-FastAPI-Cache"] == "HIT"
    assert alice_again.json() == alice.json()
    assert bob_again.json() == bob.json()
    assert calls["n"] == 2


def test_opt_in_isolates_same_authorization_different_cookie() -> None:
    init_cache()
    app, calls, _ = build_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        alice = client.get(
            "/me",
            headers={
                "Authorization": "Bearer shared",
                "Cookie": "session=alice",
            },
        )
        bob = client.get(
            "/me",
            headers={
                "Authorization": "Bearer shared",
                "Cookie": "session=bob",
            },
        )
        alice_again = client.get(
            "/me",
            headers={
                "Authorization": "Bearer shared",
                "Cookie": "session=alice",
            },
        )
        bob_again = client.get(
            "/me",
            headers={
                "Authorization": "Bearer shared",
                "Cookie": "session=bob",
            },
        )

    assert alice.headers["X-FastAPI-Cache"] == "MISS"
    assert bob.headers["X-FastAPI-Cache"] == "MISS"
    assert alice_again.headers["X-FastAPI-Cache"] == "HIT"
    assert bob_again.headers["X-FastAPI-Cache"] == "HIT"
    assert alice_again.json() == alice.json()
    assert bob_again.json() == bob.json()
    assert alice.json()["cookie"] == "session=alice"
    assert bob.json()["cookie"] == "session=bob"
    assert calls["n"] == 2


def test_opt_in_isolates_same_cookie_different_authorization() -> None:
    init_cache()
    app, calls, _ = build_app(
        cache_authenticated=True,
        key_builder=auth_key_builder,
    )

    with TestClient(app) as client:
        alice = client.get(
            "/me",
            headers={
                "Authorization": "Bearer alice",
                "Cookie": "session=shared",
            },
        )
        bob = client.get(
            "/me",
            headers={
                "Authorization": "Bearer bob",
                "Cookie": "session=shared",
            },
        )
        alice_again = client.get(
            "/me",
            headers={
                "Authorization": "Bearer alice",
                "Cookie": "session=shared",
            },
        )
        bob_again = client.get(
            "/me",
            headers={
                "Authorization": "Bearer bob",
                "Cookie": "session=shared",
            },
        )

    assert alice.headers["X-FastAPI-Cache"] == "MISS"
    assert bob.headers["X-FastAPI-Cache"] == "MISS"
    assert alice_again.headers["X-FastAPI-Cache"] == "HIT"
    assert bob_again.headers["X-FastAPI-Cache"] == "HIT"
    assert alice_again.json() == alice.json()
    assert bob_again.json() == bob.json()
    assert alice.json()["authorization"] == "Bearer alice"
    assert bob.json()["authorization"] == "Bearer bob"
    assert calls["n"] == 2


def test_reset_restores_default_auth_policy() -> None:
    init_cache(cache_authenticated=True, key_builder=auth_key_builder)
    assert FastAPICache.get_cache_authenticated() is True

    FastAPICache.reset()
    assert FastAPICache.get_cache_authenticated() is False

    init_cache()
    app, calls, _ = build_app()

    with TestClient(app) as client:
        first = client.get("/me", headers={"Authorization": "Bearer alice"})
        second = client.get("/me", headers={"Authorization": "Bearer alice"})

    assert "X-FastAPI-Cache" not in first.headers
    assert "X-FastAPI-Cache" not in second.headers
    assert calls["n"] == 2


def test_no_request_context_keeps_caching() -> None:
    init_cache(cache_authenticated=True)

    calls = {"n": 0}

    @cache(expire=60)
    async def value() -> Dict[str, int]:
        calls["n"] += 1
        return {"n": calls["n"]}

    async def run_twice() -> Tuple[Any, Any]:
        return await value(), await value()

    first, second = asyncio.run(run_twice())

    assert first == second == {"n": 1}
    assert calls["n"] == 1


def test_legacy_entry_survives_until_namespace_invalidated() -> None:
    init_cache()
    app, calls, endpoint = build_app()
    legacy_key = default_key_builder(endpoint, "auth-test:", args=(), kwargs={})
    legacy_value = JsonCoder.encode(
        {"authorization": "Bearer alice", "cookie": None, "n": 1}
    )
    InMemoryBackend._store[legacy_key] = Value(  # pyright: ignore[reportPrivateUsage]
        legacy_value,
        int(time.time()) + 60,
    )

    with TestClient(app) as client:
        public = client.get("/me")
        assert public.json()["authorization"] == "Bearer alice"
        assert calls["n"] == 0

        _clear_store()
        after_clear = client.get("/me")

    assert after_clear.json()["authorization"] is None
    assert after_clear.headers["X-FastAPI-Cache"] == "MISS"
    assert calls["n"] == 1

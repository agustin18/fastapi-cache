import asyncio
import hashlib
import logging
from contextvars import ContextVar
from typing import Any, Callable, Dict, Generator, Optional, Tuple

import pytest
from fastapi import Depends, FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.testclient import TestClient

from fastapi_cache import (
    FastAPICache,
    JsonCoder,
    KeyBuilder,
    default_key_builder,
)
from fastapi_cache.backends.inmemory import InMemoryBackend, Value
from fastapi_cache.coder import PickleCoder
from fastapi_cache.decorator import cache


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    FastAPICache.reset()
    yield
    FastAPICache.reset()


def init_cache(
    cache_authenticated: bool = False,
    key_builder: KeyBuilder = default_key_builder,
) -> InMemoryBackend:
    backend = InMemoryBackend()
    FastAPICache.init(
        backend,
        prefix="auth-test",
        cache_authenticated=cache_authenticated,
        key_builder=key_builder,
    )
    return backend


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
        super().__init__()
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
    app, calls, _ = build_app(key_builder=auth_key_builder)

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
    app, calls, _ = build_app(key_builder=auth_key_builder)

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
    app, calls, _ = build_app(key_builder=auth_key_builder)

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
    app, calls, _ = build_app(key_builder=auth_key_builder)

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


def test_explicit_request_does_not_serve_legacy_shared_entry() -> None:
    backend = init_cache()
    app, calls, endpoint = build_app()
    legacy_key = default_key_builder(endpoint, "auth-test:", args=(), kwargs={})
    legacy_value = JsonCoder.encode(
        {"authorization": "Bearer alice", "cookie": None, "n": 1}
    )
    backend._store[legacy_key] = Value(  # pyright: ignore[reportPrivateUsage]
        legacy_value,
        None,
    )

    with TestClient(app) as client:
        public = client.get("/me")
        assert public.json()["authorization"] is None
        assert "X-FastAPI-Cache" not in public.headers
        assert calls["n"] == 1
        # Do not touch unrelated entries in the shared backend.
        assert legacy_key in backend._store  # pyright: ignore[reportPrivateUsage]

        backend._store.clear()  # pyright: ignore[reportPrivateUsage]
        after_clear = client.get("/me")

    assert after_clear.json()["authorization"] is None
    assert "X-FastAPI-Cache" not in after_clear.headers
    assert calls["n"] == 2


@pytest.mark.parametrize("field", ["Authorization", "Cookie"])
def test_duplicate_credential_fields_bypass_default_cache(field: str) -> None:
    backend = SpyBackend()
    FastAPICache.init(backend, prefix="duplicate-auth")
    principal: ContextVar[str] = ContextVar("synthetic-principal", default="anon")
    app = FastAPI()

    async def authenticate(request: Request) -> None:
        values = request.headers.getlist(field)
        # Model an upstream parser that uses the last non-empty value.
        principal.set(next((v for v in reversed(values) if v), "anon"))

    @app.get("/me", dependencies=[Depends(authenticate)])
    @cache(expire=60)
    async def me() -> Dict[str, str]:
        return {"principal": principal.get()}

    with TestClient(app) as client:
        public = client.get("/me")
        alice = client.get("/me", headers=[(field, ""), (field, "alice")])
        bob = client.get("/me", headers=[(field, "bob"), (field, "")])
        again = client.get("/me")

    assert public.json() == again.json() == {"principal": "anon"}
    assert alice.json() == {"principal": "alice"}
    assert bob.json() == {"principal": "bob"}
    assert "X-FastAPI-Cache" not in alice.headers
    assert "X-FastAPI-Cache" not in bob.headers
    assert backend.get_with_ttl_calls == 2
    assert backend.set_calls == 1


@pytest.mark.parametrize("field", ["Authorization", "Cookie"])
@pytest.mark.parametrize("returned_response", [False, True])
def test_authenticated_opt_in_keeps_http_cache_private(
    field: str, returned_response: bool
) -> None:
    init_cache()
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/me")
    @cache(
        expire=60,
        cache_authenticated=True,
        key_builder=auth_key_builder,
        coder=PickleCoder if returned_response else JsonCoder,
    )
    async def me(request: Request) -> Any:
        calls["n"] += 1
        payload = {"principal": request.headers.get(field, "anon")}
        if returned_response:
            return JSONResponse(payload)
        return payload

    with TestClient(app) as client:
        first = client.get("/me", headers={field: "alice"})
        hit = client.get("/me", headers={field: "alice"})
        conditional = client.get(
            "/me", headers={field: "alice", "If-None-Match": first.headers["etag"]}
        )
        other = client.get("/me", headers={field: "bob"})
        anon = client.get("/me")
        anon_hit = client.get("/me")

    assert first.json() == hit.json() == {"principal": "alice"}
    assert other.json() == {"principal": "bob"}
    assert anon.json() == anon_hit.json() == {"principal": "anon"}
    assert conditional.status_code == 304
    assert conditional.content == b""
    assert calls["n"] == 3
    responses = (first, hit, conditional, other, anon, anon_hit)
    assert [r.headers["X-FastAPI-Cache"] for r in responses] == [
        "MISS", "HIT", "HIT", "MISS", "MISS", "HIT",
    ]
    assert all(r.headers["cache-control"] == "private, no-store" for r in responses)

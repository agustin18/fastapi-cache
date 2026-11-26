"""Opt-in, borrowed application cache configuration and lifecycle."""

import asyncio
import hashlib
import math
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional, Type

from starlette.applications import Starlette
from starlette.requests import Request

from fastapi_cache._backend_contract import Capability, backend_capabilities
from fastapi_cache.coder import Coder, JsonCoder
from fastapi_cache.key_builder import default_key_builder
from fastapi_cache.types import Backend, KeyBuilder

_ROOT = "__fastapi_cache_app_v1__"
_SLOT = "_fastapi_cache_app_handle_v1"
_SCOPE_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_ABSENT = object()


class CacheScopeError(RuntimeError):
    """Invalid, missing, conflicting or inactive application cache scope."""


def _text_bytes(value: str) -> bytes:
    if not isinstance(value, str):
        raise CacheScopeError("Invalid cache scope text")
    try:
        return str.encode(value, "utf-8")
    except UnicodeEncodeError:
        raise CacheScopeError("Invalid cache scope text") from None


def _hash_text(value: str) -> str:
    return hashlib.sha256(_text_bytes(value)).hexdigest()


def _scope_prefix(scope_id: str) -> str:
    return f"{_ROOT}:{scope_id}"


def _physical_key(config: "CacheConfig", namespace: str, logical_key: str) -> str:
    if not logical_key:
        raise CacheScopeError("Invalid logical cache key")
    return f"{_scope_prefix(config.scope_id)}:{_hash_text(namespace)}:{_hash_text(logical_key)}"


@dataclass(frozen=True, init=False, repr=False)
class CacheConfig:
    """Immutable references to a borrowed backend and app-specific settings."""

    backend: Backend
    scope_id: str
    prefix: str
    expire: Optional[int]
    coder: Type[Coder]
    key_builder: KeyBuilder
    cache_status_header: str
    enable: bool
    cache_authenticated: bool

    def __init__(
        self,
        backend: Backend,
        *,
        scope_id: str,
        prefix: str = "",
        expire: Optional[int] = None,
        coder: Type[Coder] = JsonCoder,
        key_builder: KeyBuilder = default_key_builder,
        cache_status_header: str = "X-FastAPI-Cache",
        enable: bool = True,
        cache_authenticated: bool = False,
    ) -> None:
        object.__setattr__(self, "backend", backend)
        object.__setattr__(self, "scope_id", scope_id)
        object.__setattr__(self, "prefix", prefix)
        object.__setattr__(self, "expire", expire)
        object.__setattr__(self, "coder", coder)
        object.__setattr__(self, "key_builder", key_builder)
        object.__setattr__(self, "cache_status_header", cache_status_header)
        object.__setattr__(self, "enable", enable)
        object.__setattr__(self, "cache_authenticated", cache_authenticated)


def _validate_config(config: CacheConfig) -> None:
    if not isinstance(config, CacheConfig):
        raise CacheScopeError("Invalid cache configuration")
    if type(config.scope_id) is not str or not _SCOPE_ID.fullmatch(config.scope_id):
        raise CacheScopeError("Invalid cache scope identifier")
    _text_bytes(config.prefix)
    if not isinstance(config.enable, bool) or not isinstance(config.cache_authenticated, bool):
        raise CacheScopeError("Invalid cache configuration")
    if config.expire is not None and type(config.expire) is not int:
        raise CacheScopeError("Invalid cache configuration")
    if not isinstance(config.coder, type) or not issubclass(config.coder, Coder):
        raise CacheScopeError("Invalid cache configuration")
    if not callable(config.key_builder):
        raise CacheScopeError("Invalid cache configuration")
    if type(config.cache_status_header) is not str or not config.cache_status_header:
        raise CacheScopeError("Invalid cache configuration")
    _text_bytes(config.cache_status_header)
    if backend_capabilities(config.backend).app_scope is not Capability.SUPPORTED:
        raise CacheScopeError("Unsupported app cache backend")


class CacheHandle:
    """One app, one loop, one generation. Never owns the supplied backend."""

    def __init__(self, config: CacheConfig) -> None:
        self._config = config
        self._state = "NEW"
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._app: Optional[Starlette] = None
        self._drained: Optional[asyncio.Future[None]] = None
        self._leases = 0
        self._binding_lost = False

    async def start(self, app: Starlette) -> None:
        if self._state != "NEW":
            raise CacheScopeError("Cache handle cannot be started")
        loop = asyncio.get_running_loop()
        _validate_config(self._config)
        if not isinstance(app, Starlette) or getattr(app.state, _SLOT, _ABSENT) is not _ABSENT:
            raise CacheScopeError("Cache app binding is unavailable")
        drained: asyncio.Future[None] = loop.create_future()
        setattr(app.state, _SLOT, self)
        self._loop = loop
        self._app = app
        self._drained = drained
        self._state = "ACTIVE"

    def _check_loop(self) -> None:
        if self._loop is not asyncio.get_running_loop():
            raise CacheScopeError("Cache handle belongs to another event loop")

    def _check_binding(self) -> None:
        if self._app is None or getattr(self._app.state, _SLOT, _ABSENT) is not self:
            raise CacheScopeError("Cache app binding is unavailable")

    @contextmanager
    def _lease(self) -> Iterator[CacheConfig]:
        if self._state != "ACTIVE":
            raise CacheScopeError("Cache handle is not active")
        self._check_loop()
        self._check_binding()
        self._leases += 1
        try:
            yield self._config
        finally:
            self._leases -= 1
            if self._state == "DRAINING" and self._leases == 0:
                self._finish()

    def _finish(self) -> None:
        app = self._app
        drained = self._drained
        assert app is not None and drained is not None  # noqa: S101
        if getattr(app.state, _SLOT, _ABSENT) is self:
            delattr(app.state, _SLOT)
        else:
            self._binding_lost = True
        self._app = None
        self._state = "CLOSED"
        drained.set_result(None)

    async def aclose(self, *, timeout: float = 30.0) -> None:
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise CacheScopeError("Invalid cache drain timeout")
        if self._state == "NEW":
            self._loop = asyncio.get_running_loop()
            self._state = "CLOSED"
            return
        self._check_loop()
        if self._state == "ACTIVE":
            self._state = "DRAINING"
            if self._leases == 0:
                self._finish()
        if self._state == "DRAINING":
            drained = self._drained
            assert drained is not None  # noqa: S101
            # A timeout or cancellation affects only this waiter. The last
            # admitted operation finalizes the handle; no task is spawned
            # to close resources and no borrowed client is ever closed.
            done, _ = await asyncio.wait({drained}, timeout=timeout)
            if not done:
                raise asyncio.TimeoutError("Cache drain timed out")
        if self._binding_lost:
            raise CacheScopeError("Cache app binding is unavailable")

    async def clear(
        self, *, namespace: Optional[str] = None, key: Optional[str] = None
    ) -> int:
        with self._lease() as config:
            prefix = _scope_prefix(config.scope_id)
            if key is not None:
                if namespace is not None or type(key) is not str:
                    raise CacheScopeError("Invalid scoped cache clear")
                fields = key.split(":")
                if (
                    len(fields) != 4
                    or fields[0] != _ROOT
                    or fields[1] != config.scope_id
                    or not _DIGEST.fullmatch(fields[2])
                    or not _DIGEST.fullmatch(fields[3])
                ):
                    raise CacheScopeError("Invalid scoped cache clear")
                return await config.backend.clear(key=key)
            if namespace is not None:
                prefix += ":" + _hash_text(namespace)
            return await config.backend.clear(namespace=prefix)


def _resolve_handle(request: Optional[Request], explicit: Optional[CacheHandle]) -> CacheHandle:
    if request is None:
        raise CacheScopeError("Application cache requires an HTTP request")
    app = request.scope.get("app")
    if not isinstance(app, Starlette):
        raise CacheScopeError("Cache app binding is unavailable")
    bound = getattr(app.state, _SLOT, _ABSENT)
    if (
        not isinstance(bound, CacheHandle)
        or bound._app is not app
        or (explicit is not None and explicit is not bound)
    ):
        raise CacheScopeError("Cache app binding is unavailable")
    return bound

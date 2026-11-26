"""Opt-in HTTP cache failure decisions (C3), not a retry or repair API."""

from dataclasses import dataclass

from fastapi_cache.types import Backend


@dataclass(frozen=True)
class CacheFailurePolicy:
    """Independent opt-ins for an app-scoped handle; defaults are legacy."""

    strict_read: bool = False
    conservative_write: bool = False
    recover_json: bool = False

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (self.strict_read, self.conservative_write, self.recover_json)
        ):
            raise ValueError("Cache failure policy flags must be bool")


class CacheBackendReadError(RuntimeError):
    """A classified cache transport read failure in strict mode."""


def _read_error_category(backend: Backend, exc: Exception) -> str:
    """Recognize exact Redis transport classes, not auth/config/programmer errors."""
    from fastapi_cache._backend_contract import Capability, backend_capabilities

    if backend_capabilities(backend).ownership == "borrowed" and (
        backend_capabilities(backend).app_scope is Capability.SUPPORTED
    ):
        from redis.exceptions import ConnectionError as RedisConnectionError
        from redis.exceptions import TimeoutError as RedisTimeoutError

        if type(exc) in (RedisConnectionError, ConnectionError):
            return "connection"
        if type(exc) in (RedisTimeoutError, TimeoutError):
            return "timeout"
    return "unclassified"

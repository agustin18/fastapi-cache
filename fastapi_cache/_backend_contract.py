"""Internal D4 adapter capabilities; not runtime service discovery."""

import sys
from dataclasses import dataclass
from enum import Enum

from fastapi_cache.types import Backend


class Capability(str, Enum):
    SUPPORTED = "supported"
    EXPERIMENTAL = "experimental"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BackendCapabilities:
    """Static adapter contract, conditional on documented client setup."""

    read_write: Capability
    remaining_ttl: Capability
    clear_key: Capability
    clear_namespace: Capability
    app_scope: Capability
    compare_and_delete: Capability
    ownership: str


_S = Capability.SUPPORTED
_E = Capability.EXPERIMENTAL
_N = Capability.UNSUPPORTED
_U = Capability.UNKNOWN

_INMEMORY = BackendCapabilities(_S, _S, _S, _S, _S, _N, "local")
_REDIS = BackendCapabilities(_S, _S, _S, _S, _S, _N, "borrowed")
_REDIS_CLUSTER = BackendCapabilities(_E, _E, _E, _N, _N, _N, "borrowed")
_MEMCACHED = BackendCapabilities(_E, _N, _N, _N, _N, _N, "borrowed")
_DYNAMODB = BackendCapabilities(_E, _E, _N, _N, _N, _N, "experimental")
_UNKNOWN = BackendCapabilities(_U, _U, _U, _U, _N, _U, "unknown")

_PROFILES = (
    ("fastapi_cache.backends.inmemory", "InMemoryBackend", _INMEMORY),
    ("fastapi_cache.backends.redis", "RedisBackend", _REDIS),
    ("fastapi_cache.backends.memcached", "MemcachedBackend", _MEMCACHED),
    ("fastapi_cache.backends.dynamodb", "DynamoBackend", _DYNAMODB),
)


def backend_capabilities(backend: Backend) -> BackendCapabilities:
    """Classify exact built-in adapters, without I/O or importing extras.

    Optional backend modules are already loaded for a constructed instance.
    A subclass/custom backend is unknown even if it advertises matching
    attributes or names. This is not a plugin registration API.
    """
    cls = type(backend)
    for module, name, profile in _PROFILES:
        if cls is getattr(sys.modules.get(module), name, None):
            if profile is _REDIS and getattr(backend, "is_cluster", True):
                return _REDIS_CLUSTER
            return profile
    return _UNKNOWN

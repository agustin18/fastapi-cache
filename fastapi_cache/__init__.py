from importlib.metadata import version
from typing import ClassVar, Optional, Type

from fastapi_cache.app import CacheConfig, CacheHandle, CacheScopeError
from fastapi_cache.coder import Coder, JsonCoder, TypedJsonCoder
from fastapi_cache.key_builder import default_key_builder
from fastapi_cache.types import Backend, KeyBuilder

__version__ = version("fastapi-cache-stable")  # pyright: ignore[reportUnknownVariableType]
__all__ = [
    "Backend",
    "CacheConfig",
    "CacheHandle",
    "CacheScopeError",
    "Coder",
    "FastAPICache",
    "JsonCoder",
    "KeyBuilder",
    "TypedJsonCoder",
    "default_key_builder",
]


class FastAPICache:
    _backend: ClassVar[Optional[Backend]] = None
    _prefix: ClassVar[Optional[str]] = None
    _expire: ClassVar[Optional[int]] = None
    _init: ClassVar[bool] = False
    _coder: ClassVar[Optional[Type[Coder]]] = None
    _key_builder: ClassVar[Optional[KeyBuilder]] = None
    _cache_status_header: ClassVar[Optional[str]] = None
    _enable: ClassVar[bool] = True
    _cache_authenticated: ClassVar[bool] = False

    @classmethod
    def init(
        cls,
        backend: Backend,
        prefix: str = "",
        expire: Optional[int] = None,
        coder: Type[Coder] = JsonCoder,
        key_builder: KeyBuilder = default_key_builder,
        cache_status_header: str = "X-FastAPI-Cache",
        enable: bool = True,
        cache_authenticated: bool = False,
        *,
        force: bool = False,
    ) -> None:
        if cls._init and not force:
            raise RuntimeError(
                "FastAPICache.init() was already called. Call FastAPICache.reset() "
                "before re-initializing, or pass force=True to replace the current "
                "configuration explicitly."
            )
        cls._init = True
        cls._backend = backend
        cls._prefix = prefix
        cls._expire = expire
        cls._coder = coder
        cls._key_builder = key_builder
        cls._cache_status_header = cache_status_header
        cls._enable = enable
        cls._cache_authenticated = cache_authenticated

    @classmethod
    def reset(cls) -> None:
        cls._init = False
        cls._backend = None
        cls._prefix = None
        cls._expire = None
        cls._coder = None
        cls._key_builder = None
        cls._cache_status_header = None
        cls._enable = True
        cls._cache_authenticated = False

    @classmethod
    def get_backend(cls) -> Backend:
        assert cls._backend, "You must call init first!"  # noqa: S101
        return cls._backend

    @classmethod
    def get_prefix(cls) -> str:
        assert cls._prefix is not None, "You must call init first!"  # noqa: S101
        return cls._prefix

    @classmethod
    def get_expire(cls) -> Optional[int]:
        return cls._expire

    @classmethod
    def get_coder(cls) -> Type[Coder]:
        assert cls._coder, "You must call init first!"  # noqa: S101
        return cls._coder

    @classmethod
    def get_key_builder(cls) -> KeyBuilder:
        assert cls._key_builder, "You must call init first!"  # noqa: S101
        return cls._key_builder

    @classmethod
    def get_cache_status_header(cls) -> str:
        assert cls._cache_status_header, "You must call init first!"  # noqa: S101
        return cls._cache_status_header

    @classmethod
    def get_enable(cls) -> bool:
        return cls._enable

    @classmethod
    def get_cache_authenticated(cls) -> bool:
        return cls._cache_authenticated

    @classmethod
    async def clear(
        cls, namespace: Optional[str] = None, key: Optional[str] = None
    ) -> int:
        assert (  # noqa: S101
            cls._backend and cls._prefix is not None
        ), "You must call init first!"
        if namespace is not None or key is None:
            effective_namespace = cls._prefix + (
                ":" + namespace if namespace else ""
            )
            if not effective_namespace:
                return 0
            return await cls._backend.clear(namespace=effective_namespace)
        return await cls._backend.clear(key=key)

import hashlib
import logging
import re
import sys
from functools import wraps
from inspect import Parameter, Signature, isawaitable, iscoroutinefunction
from typing import (
    Awaitable,
    Callable,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec

from fastapi.concurrency import run_in_threadpool
from fastapi.dependencies.utils import (
    get_typed_return_annotation,
    get_typed_signature,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_304_NOT_MODIFIED

from fastapi_cache import (
    CacheConfig,
    CacheHandle,
    CacheScopeError,
    FastAPICache,
)
from fastapi_cache.app import _physical_key, _resolve_handle, _text_bytes
from fastapi_cache.coder import Coder
from fastapi_cache.key_builder import default_key_builder
from fastapi_cache.types import KeyBuilder

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
P = ParamSpec("P")

_HTTP_FIELD_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+")
_SENSITIVE_VARY_FIELDS = {"authorization", "cookie", "proxy-authorization"}


def _normalize_vary_headers(names: Optional[Sequence[str]]) -> Tuple[str, ...]:
    """Validate opt-in HTTP field names once; never treat a string as a list."""
    if names is None:
        return ()
    if isinstance(names, (str, bytes)):
        raise TypeError("vary_headers must be a sequence of header names, not a string")
    normalized: Set[str] = set()
    for original in names:
        if not isinstance(original, str):
            raise TypeError("vary_headers entries must be strings")
        name = original.strip().lower()
        if (
            not name
            or name == "*"
            or len(name) > 128
            or _HTTP_FIELD_NAME.fullmatch(name) is None
            or name in _SENSITIVE_VARY_FIELDS
        ):
            raise ValueError(
                "vary_headers contains an invalid or credential-bearing field name"
            )
        normalized.add(name)
        if len(normalized) > 32:
            raise ValueError("vary_headers must contain no more than 32 fields")
    return tuple(sorted(normalized))


def _vary_is_covered(value: str, declared: Tuple[str, ...]) -> bool:
    """Only declared request fields can safely back a response Vary value."""
    fields = [name.strip().lower() for name in value.split(",")]
    return bool(declared) and bool(fields) and all(
        bool(name) and name in declared for name in fields
    )

R = TypeVar("R")


def _augment_signature(signature: Signature, *extra: Parameter) -> Signature:
    if not extra:
        return signature

    parameters = list(signature.parameters.values())
    variadic_keyword_params: List[Parameter] = []
    while parameters and parameters[-1].kind is Parameter.VAR_KEYWORD:
        variadic_keyword_params.append(parameters.pop())

    return signature.replace(parameters=[*parameters, *extra, *variadic_keyword_params])


def _locate_param(
    sig: Signature, dep: Parameter, to_inject: List[Parameter]
) -> Parameter:
    """Locate an existing parameter in the decorated endpoint

    If not found, returns the injectable parameter, and adds it to the to_inject list.

    """
    param = next(
        (p for p in sig.parameters.values() if p.annotation is dep.annotation), None
    )
    if param is None:
        to_inject.append(dep)
        param = dep
    return param


def _cache_control_directives(values: Iterable[str]) -> Set[str]:
    """Parse Cache-Control directive names, respecting quoted-string values."""
    directives: Set[str] = set()
    for value in values:
        start = 0
        in_quotes = False
        escaped = False
        for index, char in enumerate(value):
            if escaped:
                escaped = False
                continue
            if in_quotes and char == "\\":
                escaped = True
                continue
            if char == '"':
                in_quotes = not in_quotes
            elif char == "," and not in_quotes:
                name = value[start:index].split("=", 1)[0].strip().lower()
                if name:
                    directives.add(name)
                start = index + 1

        name = value[start:].split("=", 1)[0].strip().lower()
        if name:
            directives.add(name)
    return directives


def _uncacheable(
    request: Optional[Request], request_cache_control: Set[str], enable: Optional[bool] = None
) -> bool:
    """Determine if this request should not be cached

    Returns true if:
    - Caching has been disabled globally
    - This is not a GET request
    - The request has a Cache-Control `no-store` directive

    Authentication bypass is handled separately because it depends on the
    effective cache_authenticated setting.

    """
    if not (FastAPICache.get_enable() if enable is None else enable):
        return True
    if request is None:
        return False
    if request.method != "GET":
        return True
    return "no-store" in request_cache_control



def _route_scoped_generated_key(
    func: Callable[..., object],
    request: Request,
    key: str,
    namespace: str,
) -> Optional[str]:
    """Scope locally generated FastAPI handlers without changing normal legacy keys.

    The legacy default builder identifies a function by module and *name*.
    Different closures from a factory share that identity even when they
    return different data. functools.wraps can hide their generated names,
    so check closures *and* explicit __wrapped__ markers (including wrappers
    that capture values only through default arguments). This also rotates
    keys for ordinary module-level handlers wrapped by decorators; unwrapped
    module-level endpoints retain their original digest. Never read possibly
    contaminated pre-fix entries from detected handlers.
    """
    qualname = getattr(func, "__qualname__", "")
    # functools.wraps copies a module-level template's __qualname__ and
    # __name__ onto a generated endpoint, hiding the original factory name.
    # co_freevars catches closures, but not values bound as default arguments.
    # Explicit __wrapped__ metadata identifies those wrappers without
    # running inspect.unwrap or following potentially cyclic wrapper chains.
    code = getattr(func, "__code__", None)
    has_closure = bool(getattr(code, "co_freevars", ()))
    has_wrapper = getattr(func, "__wrapped__", None) is not None
    if (
        not has_closure
        and not has_wrapper
        and "<locals>" not in qualname
        and func.__name__ != "<lambda>"
    ):
        return key

    scope = request.scope
    path = scope.get("path")
    method = scope.get("method")
    root_path = scope.get("root_path", "")
    if (
        not isinstance(path, str)
        or not isinstance(method, str)
        or not isinstance(root_path, str)
    ):
        # Cannot establish a stable route identity: fail closed.
        return None

    # No Python object id / function repr: identical across workers and
    # stable for the same deployed route. Distinct hosts/mounts/methods/paths
    # cannot replay one another's entries through the default builder.
    route_identity = (
        # HTTP hostnames are case-insensitive; avoid needless cache
        # fragmentation between Example.COM and example.com.
        request.headers.get("host", "").lower(),
        method,
        root_path,
        path,
    )
    digest = hashlib.sha256(repr((route_identity, key)).encode()).hexdigest()
    return f"{namespace}:{digest}"


def _has_auth_headers(request: Optional[Request]) -> bool:
    """Return true when the request carries an authentication header."""
    if request is None:
        return False
    return any(
        value
        for name in ("authorization", "cookie")
        for value in request.headers.getlist(name)
    )


def _cache_control_header(seconds: Optional[int]) -> Optional[str]:
    """Return a valid Cache-Control header value, or None when it cannot be expressed."""
    if seconds is None or seconds < 0:
        return None
    return f"max-age={seconds}"


def _cache_control_blocks_storage(value: str) -> bool:
    """Return true when Cache-Control forbids storing or sharing the response."""
    for directive in value.split(","):
        name = directive.split("=", 1)[0].strip().lower()
        if name in {"no-store", "private"}:
            return True
    return False


def _response_cache_bypass(
    result: object, vary_headers: Tuple[str, ...] = ()
) -> bool:
    """Return true when a response must not be cached for safety reasons."""
    if not isinstance(result, Response):
        return False
    if result.background is not None:
        return True
    for name, value in result.headers.items():
        lower_name = name.lower()
        if lower_name == "set-cookie":
            return True
        if lower_name == "vary" and not _vary_is_covered(value, vary_headers):
            return True
        if lower_name == "cache-control" and _cache_control_blocks_storage(value):
            return True
    return False


def _injected_response_cache_bypass(
    response: Optional[Response], vary_headers: Tuple[str, ...] = ()
) -> bool:
    """Return true when the injected response carries metadata a cached value cannot reproduce."""
    if response is None:
        return False
    status_code = getattr(response, "status_code", None)
    if status_code is not None and status_code != 200:
        return True
    for name, value in response.headers.items():
        if name.lower() == "content-length":
            continue
        if name.lower() == "vary" and _vary_is_covered(value, vary_headers):
            continue
        return True
    return response.background is not None


def _etag_for(data: bytes) -> str:
    """Return a stable, quoted weak ETag for the cached representation."""
    return f'W/"{hashlib.sha256(data).hexdigest()}"'


def _parse_etag(value: str) -> Optional[str]:
    """Return the opaque tag for a valid entity-tag, or None for malformed input."""
    value = value.strip()
    if value.startswith("W/"):
        value = value[2:]
    if len(value) < 2 or value[0] != '"' or value[-1] != '"':
        return None
    opaque = value[1:-1]
    for char in opaque:
        code = ord(char)
        if code == 0x21 or 0x23 <= code <= 0x7E or 0x80 <= code <= 0xFF:
            continue
        return None
    return opaque


def _split_etag_list(value: str) -> Optional[List[str]]:
    """Split a comma-separated entity-tag list, respecting quoted strings."""
    result: List[str] = []
    current: List[str] = []
    in_quotes = False
    for char in value:
        if char == '"':
            in_quotes = not in_quotes
            current.append(char)
        elif char == "," and not in_quotes:
            result.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if in_quotes:
        return None
    result.append("".join(current).strip())
    return [item for item in result if item]


def _etag_matches(if_none_match: Optional[str], etag: str) -> bool:
    """Return true when If-None-Match matches the current weak ETag."""
    if not if_none_match:
        return False
    value = if_none_match.strip()
    if value == "*":
        return True
    candidates = _split_etag_list(value)
    if candidates is None or any(candidate == "*" for candidate in candidates):
        return False
    expected = _parse_etag(etag)
    assert expected is not None  # noqa: S101  # generated by _etag_for
    parsed_candidates: List[str] = []
    for candidate in candidates:
        parsed = _parse_etag(candidate)
        if parsed is None:
            return False
        parsed_candidates.append(parsed)
    return expected in parsed_candidates


def cache(
    expire: Optional[int] = None,
    coder: Optional[Type[Coder]] = None,
    key_builder: Optional[KeyBuilder] = None,
    namespace: str = "",
    injected_dependency_namespace: str = "__fastapi_cache",
    cache_authenticated: Optional[bool] = None,
    infer_response_model: bool = False,
    vary_headers: Optional[Sequence[str]] = None,
    *,
    scope: str = "legacy",
    handle: Optional[CacheHandle] = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[Union[R, Response]]]]:
    """
    cache all function
    :param injected_dependency_namespace:
    :param namespace:
    :param expire:
    :param coder:
    :param key_builder:
    :param cache_authenticated: opt in to caching authenticated requests; requires an
        identity-aware key_builder
    :param infer_response_model: opt in to FastAPI return-annotation response
        model inference, including FastAPI's output validation. Off by default
        to preserve legacy routes with non-Pydantic-compatible annotations.
    :param vary_headers: opt-in request field names for cache variation.
        Explicit Request/default-builder bypass remains in effect. This is
        not automatic tenant/identity detection or an Authorization override.

    :return:
    """

    if scope not in ("legacy", "app") or (
        handle is not None and (scope == "app" or not isinstance(handle, CacheHandle))
    ):
        raise CacheScopeError("Invalid cache scope options")
    app_scoped = scope == "app" or handle is not None
    if app_scoped:
        _text_bytes(namespace)
    normalized_vary_headers = _normalize_vary_headers(vary_headers)

    injected_request = Parameter(
        name=f"{injected_dependency_namespace}_request",
        annotation=Request,
        kind=Parameter.KEYWORD_ONLY,
    )
    injected_response = Parameter(
        name=f"{injected_dependency_namespace}_response",
        annotation=Response,
        kind=Parameter.KEYWORD_ONLY,
    )

    def wrapper(
        func: Callable[P, Awaitable[R]]
    ) -> Callable[P, Awaitable[Union[R, Response]]]:
        # get_typed_signature ensures that any forward references are resolved first
        wrapped_signature = get_typed_signature(func)
        to_inject: List[Parameter] = []
        request_param = _locate_param(wrapped_signature, injected_request, to_inject)
        response_param = _locate_param(wrapped_signature, injected_response, to_inject)
        # FastAPI injects Request internally on every cached route. Only an
        # explicitly declared Request can be inspected by the endpoint itself,
        # including headers/state absent from the legacy args/kwargs cache key.
        explicit_request = request_param not in to_inject
        return_type = get_typed_return_annotation(func)

        async def invoke(
            config: Optional[CacheConfig], /, *args: P.args, **kwargs: P.kwargs
        ) -> Union[R, Response]:
            async def ensure_async_func(*args: P.args, **kwargs: P.kwargs) -> R:
                """Run cached sync functions in thread pool just like FastAPI."""
                # if the wrapped function does NOT have request or response in
                # its function signature, make sure we don't pass them in as
                # keyword arguments
                kwargs.pop(injected_request.name, None)
                kwargs.pop(injected_response.name, None)

                if iscoroutinefunction(func):
                    # async, return as is.
                    # unintuitively, we have to await once here, so that caller
                    # does not have to await twice. See
                    # https://stackoverflow.com/a/59268198/532513
                    return await func(*args, **kwargs)
                else:
                    # sync, wrap in thread and return async
                    # see above why we have to await even although caller also awaits.
                    return await run_in_threadpool(func, *args, **kwargs)  # type: ignore[arg-type]

            copy_kwargs = kwargs.copy()
            request: Optional[Request] = copy_kwargs.pop(request_param.name, None)  # type: ignore[assignment]
            response: Optional[Response] = copy_kwargs.pop(response_param.name, None)  # type: ignore[assignment]
            request_cache_control: Set[str] = set()
            if request is not None:
                request_cache_control = _cache_control_directives(
                    request.headers.getlist("Cache-Control")
                )

            if _uncacheable(
                request, request_cache_control, config.enable if config is not None else None
            ) or _injected_response_cache_bypass(
                response, normalized_vary_headers
            ):
                return await ensure_async_func(*args, **kwargs)

            if normalized_vary_headers and request is None:
                # Direct @cache() function calls have no HTTP header values.
                # Do not invoke even a custom builder or construct a shared
                # fallback key when variation was explicitly requested.
                return await ensure_async_func(*args, **kwargs)

            prefix = config.prefix if config is not None else FastAPICache.get_prefix()
            has_auth_headers = _has_auth_headers(request)
            cache_authenticated_enabled = (
                cache_authenticated
                if cache_authenticated is not None
                else (config.cache_authenticated if config is not None else FastAPICache.get_cache_authenticated())
            )
            if has_auth_headers and not cache_authenticated_enabled:
                return await ensure_async_func(*args, **kwargs)

            # An opt-in identity-aware server-side cache must not imply that
            # HTTP intermediaries can reuse its responses. Even anonymous
            # requests to an opt-in endpoint may share its URL with private ones.
            private_http_cache = request is not None and cache_authenticated_enabled
            effective_coder = coder or (config.coder if config is not None else FastAPICache.get_coder())
            effective_expire = expire or (config.expire if config is not None else FastAPICache.get_expire())
            effective_key_builder = key_builder or (config.key_builder if config is not None else FastAPICache.get_key_builder())
            if (
                has_auth_headers
                and cache_authenticated_enabled
                and effective_key_builder is default_key_builder
            ):
                # Preserve the explicit auth contract even when a declared
                # Request would otherwise trigger the conservative bypass.
                raise ValueError(
                    "Authenticated caching requires a custom, identity-aware key_builder"
                )
            if (
                explicit_request
                and request is not None
                and effective_key_builder is default_key_builder
            ):
                # A Request parameter can influence returned data through
                # headers/state absent from args/kwargs. Do not serve any
                # previous unsafe shared entry or store a new one.
                return await ensure_async_func(*args, **kwargs)
            backend = config.backend if config is not None else FastAPICache.get_backend()
            cache_status_header = config.cache_status_header if config is not None else FastAPICache.get_cache_status_header()
            if_none_match = (
                request.headers.get("if-none-match")
                if request is not None
                else None
            )

            cache_key = effective_key_builder(
                func,
                f"{prefix}:{namespace}",
                request=request,
                response=response,
                args=args,
                kwargs=copy_kwargs,
            )
            if isawaitable(cache_key):
                cache_key = await cache_key
            if config is not None:
                if not cache_key:
                    raise CacheScopeError("Invalid logical cache key")
                _text_bytes(cache_key)
            assert isinstance(cache_key, str)  # noqa: S101  # assertion is a type guard

            if request is not None and effective_key_builder is default_key_builder:
                scoped_key = _route_scoped_generated_key(
                    func, request, cache_key, f"{prefix}:{namespace}"
                )
                if scoped_key is None:
                    return await ensure_async_func(*args, **kwargs)
                cache_key = scoped_key

            if normalized_vary_headers:
                # Guarded earlier, before any key builder was invoked.
                assert request is not None  # noqa: S101  # type guard
                variant = tuple(
                    (name, tuple(request.headers.getlist(name)))
                    for name in normalized_vary_headers
                )
                # Versioned namespace prevents reads of pre-opt-in cache
                # entries; hash both the original key and all field values.
                digest = hashlib.sha256(
                    repr((cache_key, variant)).encode("utf-8")
                ).hexdigest()
                cache_key = f"{prefix}:{namespace}:vary-v1:{digest}"

            if config is not None:
                cache_key = _physical_key(config, namespace, cache_key)

            try:
                ttl, cached = await backend.get_with_ttl(cache_key)
            except Exception as exc:
                logger.warning(
                    "Error retrieving cache entry for %s.%s in namespace %r "
                    "(backend error: %s)",
                    func.__module__,
                    func.__name__,
                    namespace if config is None else "<app-scoped>",
                    type(exc).__name__,
                )
                ttl, cached = 0, None

            if (
                cached is None or "no-cache" in request_cache_control
            ):  # miss or request revalidation
                result = await ensure_async_func(*args, **kwargs)
                if isinstance(result, Response) and result.status_code >= 400:
                    return result
                if _response_cache_bypass(result, normalized_vary_headers):
                    return result
                if _injected_response_cache_bypass(
                    response, normalized_vary_headers
                ):
                    return result
                if not effective_coder.can_encode(result):
                    return result
                if normalized_vary_headers and isinstance(result, Response):
                    # Apply Vary only after can_encode: JsonCoder accepts a
                    # plain JSONResponse, but rejects its custom headers.
                    # PickleCoder must also persist Vary on the Response.
                    result.headers["Vary"] = ", ".join(normalized_vary_headers)
                to_cache = effective_coder.encode(result)

                try:
                    await backend.set(cache_key, to_cache, effective_expire)
                except Exception as exc:
                    logger.warning(
                        "Error setting cache entry for %s.%s in namespace %r "
                        "(backend error: %s)",
                        func.__module__,
                        func.__name__,
                        namespace if config is None else "<app-scoped>",
                        type(exc).__name__,
                    )

                if response:
                    etag = _etag_for(to_cache)
                    headers = {
                        "ETag": etag,
                        cache_status_header: "MISS",
                    }
                    if normalized_vary_headers:
                        headers["Vary"] = ", ".join(normalized_vary_headers)
                    cache_control = (
                        "private, no-store" if private_http_cache
                        else _cache_control_header(effective_expire)
                    )
                    if cache_control is not None:
                        headers["Cache-Control"] = cache_control
                    response.headers.update(headers)

                    if _etag_matches(if_none_match, etag):
                        response.status_code = HTTP_304_NOT_MODIFIED
                        return response
                if (
                    normalized_vary_headers or private_http_cache
                ) and isinstance(result, Response):
                    # Starlette sends the returned Response, not FastAPI's
                    # injected response. Preserve the non-opt-in contract.
                    if response is not None:
                        result.headers.update(headers)

            else:  # cache hit
                # Validate cached bytes BEFORE conditional HTTP handling.
                # If-None-Match must not make undecodable bytes a valid 304.
                result = cast(
                    R, effective_coder.decode_as_type(cached, type_=return_type)
                )
                if response:
                    etag = _etag_for(cached)
                    headers = {
                        "ETag": etag,
                        cache_status_header: "HIT",
                    }
                    if normalized_vary_headers:
                        headers["Vary"] = ", ".join(normalized_vary_headers)
                    cache_control = (
                        "private, no-store" if private_http_cache
                        else _cache_control_header(ttl)
                    )
                    if cache_control is not None:
                        headers["Cache-Control"] = cache_control
                    response.headers.update(headers)

                    if _etag_matches(if_none_match, etag):
                        response.status_code = HTTP_304_NOT_MODIFIED
                        return response

                if (
                    normalized_vary_headers or private_http_cache
                ) and isinstance(result, Response):
                    # PickleCoder can restore a Response directly. Metadata
                    # attached only to the injected response is not sent.
                    if response is not None:
                        result.headers.update(headers)

            return result

        @wraps(func)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> Union[R, Response]:
            if not app_scoped:
                return await invoke(None, *args, **kwargs)
            request: Optional[Request] = kwargs.get(request_param.name)  # type: ignore[assignment]
            selected = _resolve_handle(request, handle)
            with selected._lease() as config:
                return await invoke(config, *args, **kwargs)

        # FastAPI's get_typed_signature omits the return annotation. Enabling
        # inference can make previously valid annotations (e.g. Union[Response,
        # dict]) fail route registration, so preserve the legacy default.
        response_signature = wrapped_signature
        if infer_response_model and return_type is not None:
            response_signature = wrapped_signature.replace(
                return_annotation=return_type
            )
        inner.__signature__ = _augment_signature(response_signature, *to_inject)  # type: ignore[attr-defined]

        return inner

    return wrapper

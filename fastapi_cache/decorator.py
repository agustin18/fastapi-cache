import hashlib
import logging
import sys
from functools import wraps
from inspect import Parameter, Signature, isawaitable, iscoroutinefunction
from typing import (
    Awaitable,
    Callable,
    List,
    Optional,
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

from fastapi_cache import FastAPICache
from fastapi_cache.coder import Coder
from fastapi_cache.key_builder import default_key_builder
from fastapi_cache.types import KeyBuilder

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
P = ParamSpec("P")
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


def _uncacheable(request: Optional[Request]) -> bool:
    """Determine if this request should not be cached

    Returns true if:
    - Caching has been disabled globally
    - This is not a GET request
    - The request has a Cache-Control header with a value of "no-store"

    Authentication bypass is handled separately because it depends on the
    effective cache_authenticated setting.

    """
    if not FastAPICache.get_enable():
        return True
    if request is None:
        return False
    if request.method != "GET":
        return True
    return request.headers.get("Cache-Control") == "no-store"


def _has_auth_headers(request: Optional[Request]) -> bool:
    """Return true when the request carries an authentication header."""
    if request is None:
        return False
    return bool(request.headers.get("Authorization")) or bool(
        request.headers.get("Cookie")
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


def _response_cache_bypass(result: object) -> bool:
    """Return true when a response must not be cached for safety reasons."""
    if not isinstance(result, Response):
        return False
    if result.background is not None:
        return True
    for name, value in result.headers.items():
        lower_name = name.lower()
        if lower_name == "set-cookie":
            return True
        if lower_name == "cache-control" and _cache_control_blocks_storage(value):
            return True
    return False


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

    :return:
    """

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
        return_type = get_typed_return_annotation(func)

        @wraps(func)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> Union[R, Response]:
            nonlocal coder
            nonlocal expire

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

            if _uncacheable(request):
                return await ensure_async_func(*args, **kwargs)

            prefix = FastAPICache.get_prefix()
            has_auth_headers = _has_auth_headers(request)
            cache_authenticated_enabled = (
                cache_authenticated
                if cache_authenticated is not None
                else FastAPICache.get_cache_authenticated()
            )
            if has_auth_headers and not cache_authenticated_enabled:
                return await ensure_async_func(*args, **kwargs)

            coder = coder or FastAPICache.get_coder()
            expire = expire or FastAPICache.get_expire()
            effective_key_builder = key_builder or FastAPICache.get_key_builder()
            if (
                has_auth_headers
                and cache_authenticated_enabled
                and effective_key_builder is default_key_builder
            ):
                raise ValueError(
                    "Authenticated caching requires a custom, identity-aware key_builder"
                )
            backend = FastAPICache.get_backend()
            cache_status_header = FastAPICache.get_cache_status_header()
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
            assert isinstance(cache_key, str)  # noqa: S101  # assertion is a type guard

            try:
                ttl, cached = await backend.get_with_ttl(cache_key)
            except Exception as exc:
                logger.warning(
                    "Error retrieving cache entry for %s.%s in namespace %r "
                    "(backend error: %s)",
                    func.__module__,
                    func.__name__,
                    namespace,
                    type(exc).__name__,
                )
                ttl, cached = 0, None

            if cached is None  or (request is not None and request.headers.get("Cache-Control") == "no-cache") :  # cache miss
                result = await ensure_async_func(*args, **kwargs)
                if isinstance(result, Response) and result.status_code >= 400:
                    return result
                if _response_cache_bypass(result):
                    return result
                if not coder.can_encode(result):
                    return result
                to_cache = coder.encode(result)

                try:
                    await backend.set(cache_key, to_cache, expire)
                except Exception as exc:
                    logger.warning(
                        "Error setting cache entry for %s.%s in namespace %r "
                        "(backend error: %s)",
                        func.__module__,
                        func.__name__,
                        namespace,
                        type(exc).__name__,
                    )

                if response:
                    etag = _etag_for(to_cache)
                    headers = {
                        "ETag": etag,
                        cache_status_header: "MISS",
                    }
                    cache_control = _cache_control_header(expire)
                    if cache_control is not None:
                        headers["Cache-Control"] = cache_control
                    response.headers.update(headers)

                    if _etag_matches(if_none_match, etag):
                        response.status_code = HTTP_304_NOT_MODIFIED
                        return response

            else:  # cache hit
                if response:
                    etag = _etag_for(cached)
                    headers = {
                        "ETag": etag,
                        cache_status_header: "HIT",
                    }
                    cache_control = _cache_control_header(ttl)
                    if cache_control is not None:
                        headers["Cache-Control"] = cache_control
                    response.headers.update(headers)

                    if _etag_matches(if_none_match, etag):
                        response.status_code = HTTP_304_NOT_MODIFIED
                        return response

                result = cast(R, coder.decode_as_type(cached, type_=return_type))

            return result

        inner.__signature__ = _augment_signature(wrapped_signature, *to_inject)  # type: ignore[attr-defined]

        return inner

    return wrapper

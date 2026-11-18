# fastapi-cache-stable

> **Community-maintained stable fork of fastapi-cache2.**
> The latest published release is beta `0.3.0b1`, based on `v0.2.2`; this branch prepares an
> unpublished `0.3.0rc1`. Neither is recommended for production before the release gates pass.
> The `fastapi_cache` import and documented core API signatures are preserved;
> intentional behavior changes are described in [MIGRATION.md](https://github.com/agustin18/fastapi-cache/blob/stable/MIGRATION.md).
> See [COMPATIBILITY.md](COMPATIBILITY.md), [MIGRATION.md](MIGRATION.md), [SUPPORT.md](SUPPORT.md),
> [SECURITY.md](SECURITY.md) and [FORK_ORIGIN.md](FORK_ORIGIN.md). Not affiliated with the original author.
> The upcoming stable `0.3.0` release will install on Python `>=3.8,<3.14`. Python 3.8–3.10
> remain legacy functional-compatibility targets only; security support is limited to server-side
> CPython 3.11–3.13. Pyodide/browser/Node runtimes are not tested or covered by these guarantees;
> this does not claim functional incompatibility. Python 3.14 remains untested and outside this
> release's metadata range. The already-published `0.3.0b1` artifact and its metadata remain
> unchanged.

> **Implemented in this beta:** error responses are not cached, opt-in `TypedJsonCoder` for
> Pydantic v2, the `clear()` fixes, the auth/privacy bypass, the InMemory
> `expire=None`/instance-isolation fixes, the `Cache-Control` fix, the stable ETag, the
> `_spec_type` namespacing, the non-JSON response bypass, and an explicit second
> `FastAPICache.init()` call that raises unless you pass `force=True`. Memcached and DynamoDB
> remain experimental. For the target stable `0.3.0`, DynamoDB is supported only on Python
> `>=3.10`; the already-published `0.3.0b1` artifact and metadata are unchanged. See
> [MIGRATION.md](MIGRATION.md).

> **Branch model:** `stable` is the only maintained and release branch. `main` mirrors the
> upstream project and is not a second development branch.

[![pypi](https://img.shields.io/pypi/v/fastapi-cache-stable.svg?style=flat)](https://pypi.org/p/fastapi-cache-stable)
[![license](https://img.shields.io/github/license/agustin18/fastapi-cache)](https://github.com/agustin18/fastapi-cache/blob/stable/LICENSE)
[![CI](https://github.com/agustin18/fastapi-cache/actions/workflows/ci.yml/badge.svg)](https://github.com/agustin18/fastapi-cache/actions/workflows/ci.yml)

## Introduction

`fastapi-cache` is a tool to cache FastAPI endpoint and function results, with
backends supporting Redis, Memcached, and Amazon DynamoDB.

## Features

- Supports `redis`, `memcache`, `dynamodb`, and `in-memory` backends.
- Easy integration with [FastAPI](https://fastapi.tiangolo.com/).
- Inherited `ETag` and `Cache-Control` support, including conditional `If-None-Match`
  requests. `Cache-Control` emits only valid `max-age` values, and ETags are stable,
  quoted weak validators.

> **Beta caveat:** `0.3.0b1` includes the auth/privacy bypass, the InMemory
> `expire=None`/instance-isolation fixes, the `Cache-Control` fix, the stable ETag, the
> `_spec_type` namespacing, the non-JSON response bypass, and explicit re-configuration
> through `FastAPICache.reset()` or `force=True`. Memcached and DynamoDB remain
> experimental. See [COMPATIBILITY.md](COMPATIBILITY.md).

## Requirements

- FastAPI
- `redis` when using `RedisBackend`.
- `memcache` when using `MemcacheBackend`.
- For target stable `0.3.0`, `aiobotocore` and `aiohttp>=3.14.4` when using `DynamoBackend` on
  Python `>=3.10`.
- The target stable `0.3.0` does not install DynamoDB client dependencies on Python 3.8/3.9;
  Redis and InMemory remain the legacy backend options. The published `0.3.0b1` metadata is
  unchanged and is not recommended for production.

## Install

`0.3.0b1` is the latest published beta referenced here. The repository prepares an
**unpublished** `0.3.0rc1`; do not assume it is available on TestPyPI/PyPI yet.
These commands install the published beta:

```shell
> pip install "fastapi-cache-stable==0.3.0b1"
```

or

```shell
> pip install "fastapi-cache-stable[redis]==0.3.0b1"
```

or

```shell
> pip install "fastapi-cache-stable[memcache]==0.3.0b1"
```

or

```shell
> pip install "fastapi-cache-stable[dynamodb]==0.3.0b1"
```

## Migrating from fastapi-cache2

The intended low-friction upgrade is **`fastapi-cache2==0.2.2` →
`fastapi-cache-stable`**, keeping your existing `from fastapi_cache ...`
imports and usual `@cache(...)` calls. For GET/JSON with standalone Redis
or InMemory, the default key algorithm is unchanged. **Uninstall the old
distribution first:** the two packages install the same Python module and
must not coexist. Update the dependency in your application's lockfile.

This is not a promise of identical behavior in every case: authenticated
requests bypass cache by default, second `init()` calls now raise, and
`clear(key=...)` is intentionally narrower. Old private/special Redis
entries may require **targeted** invalidation. See the
[quick migration checklist](https://github.com/agustin18/fastapi-cache/blob/stable/MIGRATION.md#quick-migration-for-get-json-and-redisinmemory),
verification scenarios and rollback instructions.

## Usage

### Quick Start

Redis 7 / redis-py 4.x example. Initialize once per application lifespan,
then close owned resources and reset the process-global cache configuration
on teardown. Avoid routine use of `force=True`.

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from redis import asyncio as aioredis

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis_client = aioredis.from_url(
        "redis://localhost:6379/0", decode_responses=False
    )
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    try:
        yield
    finally:
        FastAPICache.reset()
        await redis_client.close()  # redis-py 4.x


app = FastAPI(lifespan=lifespan)


@app.get("/")
@cache(expire=60)
async def index():
    return {"hello": "world"}
```

For a process-local test fixture, use
`FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")`
after importing `InMemoryBackend` from
`fastapi_cache.backends.inmemory`. InMemory data is not shared across workers.

### Initialization

Call `FastAPICache.init()` once per process at application startup. A
second call raises `RuntimeError`; test fixtures that re-enter a lifespan
must close owned backend resources and call `FastAPICache.reset()` during
teardown. `force=True` permits **deliberate** replacement but does not
close the old connection pool or isolate multiple FastAPI apps in one process.

### Use the `@cache` decorator

If you want cache a FastAPI response transparently, you can use the `@cache`
decorator between the router decorator and the view function.

Parameter | type | default | description
------------ | ----| --------- | --------
`expire` | `int` |  | sets the caching time in seconds
`namespace` | `str` | `""` | namespace to use to store certain cache items
`coder` | `Coder` | `JsonCoder` | which coder to use, e.g. `JsonCoder`
`key_builder` | `KeyBuilder` callable | `default_key_builder` | which key builder to use
`injected_dependency_namespace` | `str` | `__fastapi_cache` | prefix for injected dependency keywords.
`cache_authenticated` | `bool` | `None` | per-endpoint override for caching authenticated requests; global default is `False`; requires an identity-aware `key_builder`.

The `cache_status_header` argument belongs to `FastAPICache.init()`, **not**
`@cache()`. It controls the `HIT` / `MISS` response header.

You can also use the `@cache` decorator on regular functions to cache their result.

### Injected Request and Response dependencies

The `cache` decorator injects dependencies for the `Request` and `Response`
objects, so that it can add cache control headers to the outgoing response, and
return a 304 Not Modified response when the incoming request has a matching
`If-None-Match` header. The ETag is a quoted weak validator derived from a stable SHA-256
digest of the cached representation; `If-None-Match` supports weak comparison,
comma-separated lists and `*`. Conditional requests are evaluated on both hits and misses,
and malformed entity-tags are ignored. This only happens if the decorated endpoint doesn't
already list these dependencies already.

The keyword arguments for these extra dependencies are named
`__fastapi_cache_request` and `__fastapi_cache_response` to minimize collisions.
Use the `injected_dependency_namespace` argument to `@cache` to change the
prefix used if those names would clash anyway.


### Supported data types

The default `JsonCoder` stores any data type that FastAPI can convert to JSON, including
Pydantic models and dataclasses. On a cache hit it returns the decoded JSON value (plain
dicts/lists), not the annotated model; this is the legacy `fastapi-cache2` behavior.

Pydantic v2 users can opt into typed restoration with `TypedJsonCoder`:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.coder import TypedJsonCoder

FastAPICache.init(backend, coder=TypedJsonCoder)
```

or per endpoint:

```python
from .models import SomeModel, create_some_model

@app.get("/foo")
@cache(expire=60, coder=TypedJsonCoder)
async def foo() -> SomeModel:
    return create_some_model()
```

`TypedJsonCoder` uses the endpoint return annotation to restore the annotated type and
propagates validation errors. It requires Pydantic v2; Pydantic v1 and annotations that
cannot be represented by a Pydantic v2 schema keep the legacy decoded behavior.

For broader type support, use `fastapi_cache.coder.PickleCoder` or implement a custom coder
(see below).

`PickleCoder` deserializes with Python's `pickle` and must only be used with a cache backend
whose contents are trusted and integrity-protected. An attacker who can alter cached bytes
may be able to execute code when those values are read. `JsonCoder` is the default.

### Response handling

`JsonCoder` caches only simple `JSONResponse` objects: status `200`, media type
`application/json`, no custom headers, and no background task. Other `Response` subclasses
are returned directly and are not cached: `StreamingResponse`, `FileResponse`,
`RedirectResponse`, plain `Response`, template responses, and `JSONResponse` objects with
metadata that would be lost on a cache hit. Custom coders can override
`Coder.can_encode()` to opt in; `PickleCoder` caches response objects it can reproduce
faithfully (`JSONResponse`, plain `Response`, `RedirectResponse`) and bypasses streaming,
file, and template responses. Responses with `Set-Cookie`, `Cache-Control: no-store` or
`Cache-Control: private`, or a background task are never cached, regardless of the coder.
If the endpoint or a dependency sets `Set-Cookie`, `Cache-Control: no-store`/`private`, a
background task, a non-`200` status, or any header other than the automatic `content-length`
on the injected `response` object, the call is not cached. This covers dict/list returns whose
final HTTP metadata comes from that object.
User payloads that contain `_spec_type` are preserved as normal data; the internal marker is
namespaced as `__fastapi_cache_spec_type__`.

### Custom coder

By default use `JsonCoder`, you can write custom coder to encode and decode cache result, just need
inherit `fastapi_cache.coder.Coder`.

```python
from typing import Any
import orjson
from fastapi.encoders import jsonable_encoder
from fastapi_cache import Coder

class ORJsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return orjson.dumps(
            value,
            default=jsonable_encoder,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
        )

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return orjson.loads(value)


@app.get("/")
@cache(expire=60, coder=ORJsonCoder)
async def index():
    return dict(hello="world")
```

### Custom key builder

By default the `default_key_builder` builtin key builder is used; this creates a
cache key from the function module and name, and the positional and keyword
arguments converted to their `repr()` representations, encoded as a MD5 hash.
You can provide your own by passing a key builder in to `@cache()`, or to
`FastAPICache.init()` to apply globally.

For example, if you wanted to use the request method, URL and query string as a cache key instead of the function identifier you could use:

```python
from starlette.requests import Request
from starlette.responses import Response


def request_key_builder(
    func,
    namespace: str = "",
    *,
    request: Request = None,
    response: Response = None,
    args=(),
    kwargs=None,
):
    if request is None:
        raise ValueError("This builder requires an HTTP Request")
    return ":".join([
        namespace,
        request.method.lower(),
        request.url.path,
        repr(sorted(request.query_params.items()))
    ])


@app.get("/")
@cache(expire=60, key_builder=request_key_builder)
async def index():
    return dict(hello="world")
```

This request-URL builder is appropriate for **public** data only. A custom
builder must include *every* value that affects the response, particularly
validated identity, tenant and permissions when authenticated caching is
explicitly enabled. DB session objects with changing `repr()` values can
otherwise produce perpetual misses; see the migration checklist.

### Authenticated requests

By default, requests with a non-empty `Authorization` or `Cookie` header bypass the cache:
the endpoint runs normally and nothing is read from or written to the backend. Public
requests keep caching.

This is a conservative default. Session cookies are covered because they use the `Cookie`
header. Empty headers are treated as unauthenticated. Functions decorated without a
`Request` parameter have no HTTP identity context and keep using the cache.

To cache authenticated responses, opt in explicitly and provide a key builder that includes
the identity:

```python
import hashlib
import hmac
import os

from starlette.requests import Request

from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

CACHE_KEY_SECRET = os.environ["CACHE_KEY_SECRET"].encode()


def identity_key_builder(
    func,
    namespace: str = "",
    *,
    request: Request = None,
    response=None,
    args,
    kwargs,
):
    identity = ""
    if request is not None:
        identity = "|".join(
            [
                request.headers.get("Authorization", ""),
                request.headers.get("Cookie", ""),
                request.headers.get("X-Tenant-Id", ""),
            ]
        )
    key_material = f"{identity}|{args}|{kwargs}"
    digest = hmac.new(
        CACHE_KEY_SECRET,
        key_material.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{namespace}:{func.__module__}:{func.__name__}:{digest}"


FastAPICache.init(backend, cache_authenticated=True, key_builder=identity_key_builder)


@app.get("/me")
@cache(expire=60)
async def me(request: Request):
    ...
```

The key builder must include every dimension that affects the response: token, session,
tenant, permissions, and any other validated principal state. Prefer the principal your app
already validated over raw headers. Do not put credentials in plaintext in keys or logs; use
HMAC-SHA256 with an application secret.

If `cache_authenticated=True` is used with the default key builder, an authenticated request
raises `ValueError` before the cache is accessed. The flag can also be set per endpoint:
`@cache(cache_authenticated=True, key_builder=identity_key_builder)`.

The automatic bypass only detects `Authorization` and `Cookie`. If your app uses `X-API-Key`,
proxy-injected headers, `request.state`, or internal dependencies, review your cache strategy.
`cache_authenticated=True` does not make an unsafe key builder safe.

This protects the application cache. It does not configure CDN, reverse-proxy, or browser
caching.

**Upgrading from `0.3.0a1` or earlier:** old entries written for authenticated requests may
remain under the default key. Clear or rotate the cache namespace before deploying, including
all instances/workers and persistent Redis caches. The bypass is not retroactive.

## Backend notes

### InMemoryBackend

The `InMemoryBackend` stores cache data in memory and only deletes when an
expired key is accessed. This means that if you don't access a function after
data has been cached, the data will not be removed automatically.

`expire=None` means no expiration. Each backend instance owns its store and lock, so a new
instance does not see entries from another instance. Do not share one instance across event
loops or threads; use one instance per loop/thread. Subclasses that override `__init__()`
must call `super().__init__()`. InMemory is process-local; use Redis or Memcached for
cross-process sharing. `expire=0` keeps the legacy fallback to the global `expire` value.
`get_with_ttl` returns `-1` for no-expiration entries; the decorator omits `max-age` for
those entries and for `expire=None`.

### RedisBackend

When using the Redis backend, please make sure you pass in a redis client that does [_not_ decode responses][redis-decode] (`decode_responses` **must** be `False`, which is the default). Cached data is stored as `bytes` (binary), decoding these in the Redis client would break caching.

`RedisBackend` is tested with Redis 7 and redis-py 4.6.0. The `redis` extra pins
`redis = "^4.2.0rc1"`, which does not include redis-py 5/6; those clients are untested.
Broader Redis client/server support is targeted for a later release.

[redis-decode]: https://redis-py.readthedocs.io/en/latest/examples/connection_examples.html#by-default-Redis-return-binary-responses,-to-decode-them-use-decode_responses=True

## Tests and coverage

```shell
coverage run -m pytest
coverage html
xdg-open htmlcov/index.html
```

## License

This project is licensed under the [Apache-2.0](https://github.com/agustin18/fastapi-cache/blob/stable/LICENSE) License.

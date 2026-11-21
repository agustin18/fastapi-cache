# fastapi-cache-stable

> Community-maintained fork of [fastapi-cache2](https://pypi.org/project/fastapi-cache2/).
> The Python import stays `fastapi_cache`; intentional safety/behavior changes
> are described in [MIGRATION.md](https://github.com/agustin18/fastapi-cache/blob/stable/MIGRATION.md).
>
> **Latest published stable:** [0.5.0 on PyPI](https://pypi.org/project/fastapi-cache-stable/0.5.0/)
> (released 2026-11-21) ·
> [Release notes](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_NOTES_0.5.0.md) ·
> [Release evidence](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_STATUS_0.5.0.md) ·
> [Quickstart](https://github.com/agustin18/fastapi-cache/blob/stable/docs/QUICKSTART.md) ·
> [Migration](https://github.com/agustin18/fastapi-cache/blob/stable/MIGRATION.md) ·
> [Compatibility](https://github.com/agustin18/fastapi-cache/blob/stable/COMPATIBILITY.md) ·
> [Security](https://github.com/agustin18/fastapi-cache/blob/stable/SECURITY.md) ·
> [Support](https://github.com/agustin18/fastapi-cache/blob/stable/SUPPORT.md) ·
> [Changelog](https://github.com/agustin18/fastapi-cache/blob/stable/CHANGELOG.md).
> Pre-releases must be independently evaluated before production deployment.
>
> Installation: Python `>=3.8,<3.14`. CPython 3.11–3.13 (server-side) has
> security validation; Python 3.8–3.10 is functional legacy compatibility only.
> DynamoDB/Memcached remain experimental. Browser/Pyodide/Node are untested.
> Independent project, not endorsed by the upstream maintainer.
>
> `stable` is the release branch; `main` tracks upstream.

[![pypi](https://img.shields.io/pypi/v/fastapi-cache-stable.svg?style=flat)](https://pypi.org/p/fastapi-cache-stable)
[![license](https://img.shields.io/github/license/agustin18/fastapi-cache)](https://github.com/agustin18/fastapi-cache/blob/stable/LICENSE)
[![CI](https://github.com/agustin18/fastapi-cache/actions/workflows/ci.yml/badge.svg)](https://github.com/agustin18/fastapi-cache/actions/workflows/ci.yml)


### Python versions and security

**Recommended for production:** CPython **3.11–3.13**, within our tested
FastAPI/Redis/InMemory matrix. Python **3.8–3.10** stays installable and
functionally tested to support migrations from `fastapi-cache2`, but is
**legacy-only**: these EOL runtimes and their dependency stacks receive
**no security maintenance commitment**. Known issues in some Python 3.8/3.9
dependency profiles include [AnyIO TLS](https://github.com/advisories/GHSA-82r6-8w77-94w6)
and [Starlette file serving](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8).
The library does not exercise those specific paths directly, but other
application features might. **Use a newer Python and patched compatible
dependencies whenever possible.**

A vulnerability found in a package shared by this fork and the original
`fastapi-cache2` may affect *both* if a consumer resolves the same vulnerable
version and invokes the affected code. They do **not** necessarily install
the same dependency versions. In particular, the **published `fastapi-cache2==0.2.2`** and this fork
both declared redis-py **4.x** in the published 0.3.x metadata. The upstream repository's later, **unreleased**
`main` branch changed the Redis extra to **5.x**. `0.4.x` now publishes
Python-conditional redis-py ranges through 8.1.x; older `0.3.x` artifacts
remain unchanged.
See [compatibility & risk matrix](https://github.com/agustin18/fastapi-cache/blob/stable/COMPATIBILITY.md),
[security policy](https://github.com/agustin18/fastapi-cache/blob/stable/SECURITY.md) and
[legacy vulnerability explanation](https://github.com/agustin18/fastapi-cache/blob/stable/audit/security/LEGACY_SUPPORT_AND_RISKS.md).


## Choose your path

| I'm… | Start here | What you'll learn |
|---|---|---|
| **Starting from zero** | [Install in 5 minutes](docs/QUICKSTART.md) · [Visual guide source](site_docs/getting-started.md) | Pinned package, InMemory, first HIT/MISS, Redis |
| **Already on fastapi-cache2** | [Migration walkthrough](site_docs/migration.md) · [Full migration contract](MIGRATION.md) | Remove the old distribution, validate privacy, migrate namespaces, rollback |
| **Comparing features/backends** | [Feature matrix](site_docs/reference/features.md) · [Backend choice](site_docs/backends.md) | What's actually in 0.5.0 and what remains proposed |
| **Checking security** | [Tenant and request safety](site_docs/guides/privacy.md) · [Security policy](SECURITY.md) | Default auth bypass, custom headers, cache-key isolation |
| **Looking ahead** | [Next release plan](site_docs/roadmap.md) · [#86 tracker](https://github.com/agustin18/fastapi-cache/issues/86) | 0.6.0 candidates, not publication promises |

**Try it:** [one-command before/after migration demo](examples/migration/README.md) (two isolated published environments, no Redis or credentials).

**Published:** [fastapi-cache-stable 0.5.0](https://pypi.org/project/fastapi-cache-stable/0.5.0/). The new searchable site is in [site_docs/](site_docs/index.md) and has a **CI build preview**; it is not claimed to be hosted publicly until a separate deployment is approved.


## Introduction

`fastapi-cache` is a tool to cache FastAPI endpoint and function results, with
backends supporting Redis, Memcached, and Amazon DynamoDB.

## Development roadmap

The published 0.5.0 line prioritizes safe, low-friction migration over feature
count. See [the roadmap](https://github.com/agustin18/fastapi-cache/blob/stable/ROADMAP.md) and its linked issues for
maintenance and later opt-in work. Roadmap items are **not** included in 0.5.0
and are not delivery commitments.

## Features

- Same `fastapi_cache` imports and legacy default cache-key algorithm.
- Correctness fixes for cache invalidation, error responses and HTTP cache headers.
- Auth/Cookie privacy bypass by default; opt-in typed JSON decoding for Pydantic v2.
- Opt-in `vary_headers` for explicitly declared public header dimensions, with versioned hashed keys.
- Redis and InMemory backends; Memcached and DynamoDB remain experimental.
- CI across Python versions, security profiles and published-wheel Redis migration.

## Requirements

- FastAPI with a compatible Python version.
- Redis standalone verified with Python-conditional redis-py ranges: 4.x through 6.1.x on Python 3.8, through 7.0.x on 3.9, and through 8.1.x on 3.10–3.13.
- DynamoDB client extra requires Python 3.10+ and patched aiohttp.
- See [COMPATIBILITY.md](https://github.com/agustin18/fastapi-cache/blob/stable/COMPATIBILITY.md) before using optional backends.

## Install

Install the **published version** you have tested, pinned exactly:

```sh
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.5.0"
python -m pip check
```

The [0.5.0 release evidence](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_STATUS_0.5.0.md)
records the published wheel/sdist hashes and workflows. Do not treat the
repository version alone as publication evidence.

For process-local InMemory caching, omit `[redis]`. See the
[5-minute quickstart](https://github.com/agustin18/fastapi-cache/blob/stable/docs/QUICKSTART.md) for a complete example.

To evaluate a **published pre-release candidate**:

```sh
python -m pip install --pre --upgrade "fastapi-cache-stable[redis]"
```

Other extras: `[memcache]`, `[dynamodb]` (experimental), or no extra for
InMemory. Before deploying, [check PyPI](https://pypi.org/project/fastapi-cache-stable/)
and pin the exact version you've tested. Never co-install `fastapi-cache2`;
both distributions provide `fastapi_cache` files.

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

If you want to cache a FastAPI response transparently, use the `@cache`
decorator between the router decorator and the view function.

Parameter | type | default | description
------------ | ----| --------- | --------
`expire` | `int` |  | sets the caching time in seconds
`namespace` | `str` | `""` | namespace to use to store certain cache items
`coder` | `Coder` | `JsonCoder` | which coder to use, e.g. `JsonCoder`
`key_builder` | `KeyBuilder` callable | `default_key_builder` | which key builder to use
`injected_dependency_namespace` | `str` | `__fastapi_cache` | prefix for injected dependency keywords.
`cache_authenticated` | `bool` | `None` | per-endpoint override for authenticated requests; requires an identity-aware `key_builder`.
`infer_response_model` | `bool` | `False` | opt into FastAPI's response-model inference from a return annotation; can enable output validation and break invalid union/Response annotations. Disabled by default for drop-in compatibility.
`vary_headers` | `Sequence[str]` | `None` | opt into an isolated, hashed variant cache key for the **explicitly listed** HTTP request headers; it does not automatically discover tenant/identity/context state.

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

### Optional response-model inference

By default, `@cache` preserves the upstream behavior of **not** exposing
the function's return annotation as a FastAPI response model. Existing
endpoints that return mixed `Response` and data values therefore keep
registering without new Pydantic validation.

To have FastAPI infer an OpenAPI response model from a valid annotation
and validate/serialize the output, opt in explicitly:

```python
@app.get("/item")
@cache(expire=60, infer_response_model=True)
async def item() -> SomeModel:
    return create_some_model()
```

Do **not** opt in with annotations FastAPI cannot use as a response model,
for example `Union[Response, dict]`. Alternatively, set
`response_model=SomeModel` on `@app.get(...)` as with ordinary FastAPI.
This option changes schema and response validation, not stored cache keys.

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
on the injected `response` object, the call is not cached. The sole exception is an injected
`Vary` header whose fields are all covered by explicitly declared `vary_headers`;
other metadata still bypasses. This covers dict/list returns whose final HTTP metadata
comes from that object. A returned `JSONResponse` with custom `Vary` remains uncacheable
under `JsonCoder` because its headers cannot be faithfully restored on a hit.
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

### Explicit request-header variants (0.5.0)

**Versioned API:** `vary_headers` was introduced in published 0.5.0.
It is **not part of published 0.4.1**. Pin the tested 0.5.0 distribution and
review your application-specific cache-key/identity and namespace-migration
requirements below.

For anonymous/public endpoints that depend on a **known** header through a
dependency, middleware, or `contextvars`, opt in to a header-specific key:

```python
from contextvars import ContextVar
from fastapi import Depends, Request

locale_context = ContextVar("locale", default="en")


async def resolve_locale(request: Request) -> None:
    locale_context.set(request.headers.get("Accept-Language", "en"))


@app.get("/localized", dependencies=[Depends(resolve_locale)])
@cache(expire=60, namespace="localized-v2",
       vary_headers=("Accept-Language",))
async def localized():
    return {"locale": locale_context.get()}
```

This is an **explicit allowlist**, not automatic header detection. Names are
case-normalized and validated; multiple field occurrences, their order, and
missing versus empty fields have distinct keys. Header values are hashed into
a `:vary-v1:` key scoped under the normal cache namespace, not written as
plaintext. The generated HTTP `Vary` header is returned on MISS, HIT and 304
for configured cacheable requests. **An HTTP `Vary` response header alone
never partitions the library's internal cache.** If the endpoint emits a
`Vary` field not present in `vary_headers`, the response bypasses storage.

For a **cacheable returned `Response`**, the decorator applies generated
`Vary` to the actual returned object, not just FastAPI's injected response.
A plain `JSONResponse` is checked for `JsonCoder` eligibility *before*
the header is added; a plain `Response` with `PickleCoder` also keeps the
header on MISS and HIT. The generated ETag and cache-status headers follow
the returned object as well, and 304 responses carry `Vary`. A
`JSONResponse` that already has custom headers, including `Vary`,
still bypasses the default JSON coder.

The caller is responsible for listing **every** representation-defining
header. Application state derived from hidden `contextvars`, middleware,
non-header sources or arbitrary dependencies cannot be discovered. Using
`vary_headers=("Accept-Language",)` **does not** make an endpoint whose
response also depends on `X-Tenant` safe; include a trustworthy tenant
dimension or use a reviewed, complete custom `key_builder`. Endpoints
that explicitly declare `Request` still **bypass** the default key builder
even with `vary_headers`; use an identity- and tenant-aware custom builder
there. Only `Authorization`, `Cookie` and `Proxy-Authorization` are
explicitly rejected as credential-related `vary_headers` names. Names
like `X-API-Key`, `X-Auth-Token` and application-defined identity headers
can pass the **syntactic** name check; that is **not** a safety endorsement
or an authentication/authorization boundary. The existing
`Authorization`/`Cookie` bypass is unchanged and cannot detect every
custom authentication mechanism. Use validated identity/permissions and
a reviewed custom `key_builder` when needed. A client can choose many
distinct header values and flood the cache with variants: validate and
normalize input, rate-limit, bound cache growth and expiration. Hashing
hides the literal header value from cache keys, but does not authenticate
it, encrypt it or prevent low-entropy guesses.

New opted-in entries **cannot read pre-opt-in keys**. Clear or rotate affected
namespaces (and remove potentially unsafe historical entries) before serving
traffic; do not simply assume they will disappear safely. A shared Redis
namespace used across deployments must be migrated deliberately. See
[MIGRATION.md](MIGRATION.md#explicit-header-variation-new-opt-in-for-050).

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

**Upgrading from the legacy package or early prereleases:** old entries written for authenticated requests may
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

`0.4.x` publishes Python-conditional Redis client ranges (4.x through 6.1.x
on Python 3.8, through 7.0.x on 3.9 and through 8.1.x on 3.10–3.13). See
`COMPATIBILITY.md` and `audit/redis/REDIS_CLIENT_MATRIX_RESEARCH.md` for
real-server evidence. The older `0.3.x` artifacts remain immutable.

[redis-decode]: https://redis-py.readthedocs.io/en/latest/examples/connection_examples.html#by-default-Redis-return-binary-responses,-to-decode-them-use-decode_responses=True

## Tests and coverage

```shell
coverage run -m pytest
coverage html
xdg-open htmlcov/index.html
```

## License

This project is licensed under the [Apache-2.0](https://github.com/agustin18/fastapi-cache/blob/stable/LICENSE) License.

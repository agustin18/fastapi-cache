# Compatibility contract

`fastapi-cache-stable` is an independent, community-maintained fork of
[`fastapi-cache2`](https://pypi.org/project/fastapi-cache2/). This document defines what
"drop-in" means for this project and what we promise to keep stable.

## What "drop-in" means

- The distribution is `fastapi-cache-stable`, but the Python import remains `fastapi_cache`.
- The public names below keep their import paths and call signatures.
- The normal success path for a GET endpoint keeps the same observable behavior: cache
  miss calls the endpoint, cache hit returns the cached value, and the cache status header
  reports `MISS`/`HIT`.
- Existing `@cache(...)` and `FastAPICache.init(...)` signatures remain available for
  documented valid use cases. Intentional behavior changes, including the default
  authentication bypass and explicit repeated-initialization contract, are listed in
  [`MIGRATION.md`](MIGRATION.md).
- `FastAPICache` holds one process-global configuration. Initialize once per worker; `force=True`
  replaces it but does not close the previous backend or isolate multiple applications.
- Authenticated requests bypass the cache by default. This is an intentional privacy behavior
  change; authenticated endpoints must opt in with `cache_authenticated=True` and an
  identity-aware `key_builder` to keep caching.
- `InMemoryBackend` instances are isolated: each owns its store and lock. `expire=None` means
  no expiration. InMemory remains process-local; use a shared backend for cross-process
  caching.
- Existing custom backends, coders and key builders that implement the documented protocols
  keep working.
- Migration from `fastapi-cache2` does not require application code changes for valid legacy
  use cases, subject to the behavior changes documented in [`MIGRATION.md`](MIGRATION.md).
- Pydantic v2 users can opt into `TypedJsonCoder` for typed restoration; the default
  `JsonCoder` keeps the legacy decoded behavior. Pydantic v1 and unsupported annotations
  keep the legacy behavior.
- Stable `0.3.0` keeps functional compatibility for Python 3.8–3.10 through a pinned legacy
  CI matrix. These EOL runtimes are not part of the security-supported environment.

## Public surface

```python
from fastapi_cache import (
    Backend,
    Coder,
    FastAPICache,
    JsonCoder,
    KeyBuilder,
    TypedJsonCoder,
    default_key_builder,
)
from fastapi_cache.decorator import cache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.memcached import MemcachedBackend
from fastapi_cache.backends.dynamodb import DynamoBackend
```

### `FastAPICache`

```python
FastAPICache.init(
    backend,
    prefix="",
    expire=None,
    coder=JsonCoder,
    key_builder=default_key_builder,
    cache_status_header="X-FastAPI-Cache",
    enable=True,
    cache_authenticated=False,
)
FastAPICache.clear(namespace=None, key=None)
FastAPICache.reset()
FastAPICache.get_backend()
FastAPICache.get_prefix()
FastAPICache.get_expire()
FastAPICache.get_coder()
FastAPICache.get_key_builder()
FastAPICache.get_cache_status_header()
FastAPICache.get_enable()
FastAPICache.get_cache_authenticated()
```

### `@cache(...)`

```python
cache(
    expire=None,
    coder=None,
    key_builder=None,
    namespace="",
    injected_dependency_namespace="__fastapi_cache",
    cache_authenticated=None,
)
```

### `Backend` protocol

```python
async def get_with_ttl(key: str) -> tuple[int, bytes | None]
async def get(key: str) -> bytes | None
async def set(key: str, value: bytes, expire: int | None = None) -> None
async def clear(namespace: str | None = None, key: str | None = None) -> int
```

### `KeyBuilder` protocol

```python
def __call__(
    function,
    namespace: str = "",
    *,
    request=None,
    response=None,
    args: tuple,
    kwargs: dict,
) -> str | Awaitable[str]
```

### `Coder` protocol

```python
classmethod can_encode(value) -> bool
classmethod encode(value) -> bytes
classmethod decode(value: bytes) -> Any
classmethod decode_as_type(value: bytes, *, type_) -> Any
```

## Support levels

- **Legacy functional compatibility:** stable `0.3.0` installs on Python 3.8–3.10 and tests
  the documented legacy combinations. Those runtimes and their EOL dependency lines do not
  receive a security-support commitment.
- **Security-supported environment:** Python 3.11–3.13 with the resolver-selected FastAPI and
  Pydantic versions, plus the optional dependency profiles included in the security audit.
  Security support means investigating and addressing applicable issues in this documented
  scope; it does not certify every possible downstream dependency combination as vulnerability-free.
- **Critical legacy findings:** EOL status alone is not an applicability verdict. Critical
  advisories in legacy profiles must be assessed for package-controlled execution paths,
  mitigations and residual risk before stable.

Python 3.8, 3.9 and 3.10 are end-of-life, and Pydantic v1 is end-of-life with 1.10.27 as its
final release. Stable `0.3.0` retains the package range `>=3.8,<3.14`; Python 3.8–3.10 are
tested for legacy functional compatibility but are not security-supported. Pydantic v1 keeps
its documented legacy decoded behavior, but receives no new upstream security fixes.

## Supported matrix for `0.3.x`

> Stable `0.3.0` metadata is `python = ">=3.8,<3.14"`. Functional compatibility and security
> support are separate: Python 3.8–3.10 are legacy-tested only; security support is Python
> 3.11–3.13. Python 3.14 remains unsupported pending a full matrix.

Status definitions:

- **Verified**: tested in CI with identified versions.
- **Targeted for 0.3.0**: intended behavior, not yet guaranteed.
- **Experimental**: interface available, coverage insufficient.
- **Unsupported**: outside the compatibility contract.

| Component | Status | Notes |
|---|---|---|
| Python 3.11–3.13 | Security-supported | Full functional and security-audit matrices |
| Python 3.10 | Legacy functional compatibility | Main functional CI plus Pydantic v1 compatibility; EOL, no security-support commitment |
| Python 3.8–3.9 | Legacy functional compatibility | Pinned FastAPI/Pydantic matrix and Python 3.8 wheel smoke; EOL, no security-support commitment |
| Python 3.14 | Unsupported for `0.3.0` | Requires a full CI matrix before support is announced |
| FastAPI | Verified with 0.111.1 and current 0.x | Older 0.100.x validation is a beta gate; no upper pin yet (`fastapi = "*"`) |
| Pydantic 2.x | Verified | Typed restoration is opt-in via `TypedJsonCoder`; default `JsonCoder` keeps legacy behavior |
| Pydantic v1 | Verified for migration | Tested with 1.10.27; EOL, no new security fixes; typed restoration is not applied |
| `Response`/`JSONResponse` annotations | Legacy decoded behavior | No Pydantic schema generation; cache hits keep working |
| Redis standalone | Verified for clear semantics | Redis 7 service in CI with redis-py 4.6.0; key-only clear and namespace boundary tested. redis-py 5/6 are not supported by the current `^4.2.0rc1` constraint and are untested |
| Redis Cluster | Unsupported for namespace clear | Key-only clear is supported; namespace clear raises `NotImplementedError`; no complete namespace clearing |
| InMemory | Verified for basic operations, clear semantics, `expire=None` and instance isolation | Unit tests; each instance owns its store and lock; no size cap yet |
| Memcached | Experimental | Unit tests with a fake client; `get_with_ttl` returns a fixed `3600` instead of the real remaining time; `clear` raises `NotImplementedError` |
| DynamoDB | Experimental | Unit tests with a fake client covering get/set, TTL and the expired-entry path; `clear` raises `NotImplementedError`; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

> Redis results in `0.3.0a2` cover Redis 7 with redis-py 4.6.0. Other client or server
> versions are not verified; do not infer support from the Redis 7 job alone.

### `0.3.0a1` status

Implemented: error responses, opt-in `TypedJsonCoder`, `clear()` key/namespace semantics,
Redis Cluster namespace `NotImplementedError`, and the legacy compatibility matrix.

### `0.3.0a2` status

Implemented in `0.3.0a2`: authenticated requests bypass the
cache by default; opt-in with `cache_authenticated=True` and an identity-aware `key_builder`.
Opting in with the default key builder raises `ValueError` for authenticated requests.
`InMemoryBackend` instances are isolated, and `expire=None` means no expiration. The
decorator emits `Cache-Control: max-age` only for valid, non-negative expiry values; it
omits `max-age` for `expire=None` and no-expiration hits. `expire=0` keeps the legacy
fallback to the global `expire` value. ETags are quoted weak validators derived from a
stable SHA-256 digest; `If-None-Match` uses weak comparison, supports lists and `*`, is
evaluated on hits and misses, and ignores malformed entity-tags. `_spec_type` user payloads
are preserved via a namespaced internal marker. `JsonCoder` caches only simple `200`
`application/json` `JSONResponse` objects; other responses are bypassed unless the coder's
`can_encode` supports them. Responses with `Set-Cookie`, `Cache-Control: no-store/private`,
or a background task are never cached. The injected `response` object is checked before a
cache read and before a write; those directives, a non-`200` status, or any header other than
the automatic `content-length` bypass the cache for dict/list returns.

Merged on `stable`, ships in `0.3.0b1`: a second `FastAPICache.init()` call raises
`RuntimeError` unless you pass `force=True`. In the published `0.3.0a2` it is still a silent
no-op. Still targeted for later pre-releases: the Redis client/server matrix.

### Clear semantics

- `clear(key=...)` deletes exactly that key. Pass the full key as stored by the backend.
- `clear(namespace=...)` requires the `:` namespace boundary and includes nested namespaces.
- `clear()` clears the configured prefix; with an empty prefix it is a no-op.
- If both `namespace` and `key` are provided, `namespace` wins.
- Namespace clear is best-effort, not atomic. Keys added during a Redis `SCAN` may survive.
- Redis standalone uses `SCAN` + `UNLINK`; Redis Cluster namespace clear raises
  `NotImplementedError`; use key-only clear or flush the database out of band.
- Memcached and DynamoDB do not implement `clear`.
- `clear()` is an administrative invalidation operation. Do not accept arbitrary keys or
  namespaces from untrusted users.

## Intentional behavior changes

These are bug fixes targeted for `0.3.0`. The error-response, typed-decode and
clear-semantics fixes are implemented in `0.3.0a1`; the auth/privacy, InMemory,
`Cache-Control`, ETag, `_spec_type` and response-caching fixes are implemented in `0.3.0a2`;
the second-`init` row is merged on `stable` and ships in `0.3.0b1`. Each one is documented in [`MIGRATION.md`](MIGRATION.md) and covered by a
regression test when implemented.

| Version | Change | Why | Status |
|---|---|---|---|
| 0.3.0 | Error `Response` objects (status >= 400) are not cached | A cached 404 could be returned as 200 | Implemented in `0.3.0a1` |
| 0.3.0 | Opt-in `TypedJsonCoder` decodes cached JSON into the annotated return type on Pydantic v2 | Default `JsonCoder` and Pydantic v1 keep the legacy decoded behavior; `TypedJsonCoder` propagates validation errors | Implemented in `0.3.0a1` |
| 0.3.0 | Authenticated requests bypass the cache by default | Prevent cross-user response reuse | Implemented in `0.3.0a2` |
| 0.3.0 | ETag is stable across processes and correctly quoted | `hash()` is randomized per process and the old header was invalid | Implemented in `0.3.0a2` |
| 0.3.0 | `clear(key=...)` deletes only that key | It used to delete the whole prefix namespace | Implemented in `0.3.0a1` |
| 0.3.0 | `clear("app:user")` does not delete `app:users` | Namespace matching requires the `:` boundary | Implemented in `0.3.0a1` |
| 0.3.0 | Redis Cluster namespace clear raises `NotImplementedError` | Partial/unsafe clearing was not reliable | Implemented in `0.3.0a1` |
| 0.3.0 | `expire=None` means no expiration in `InMemoryBackend` | It used to expire almost immediately | Implemented in `0.3.0a2` |
| 0.3.0 | `InMemoryBackend` instances do not share state | The class-level store leaked entries between instances | Implemented in `0.3.0a2` |
| 0.3.0 | `Cache-Control` never emits `max-age=None` or `max-age=-1` | Invalid headers | Implemented in `0.3.0a2` |
| 0.3.0 | User payloads with a `_spec_type` key are not interpreted as internal metadata | The marker collided with user data | Implemented in `0.3.0a2` |
| 0.3.0 | Only simple `JSONResponse` objects are cached by `JsonCoder`; other responses bypass | Status/headers/body were lost or corrupted | Implemented in `0.3.0a2` |
| 0.3.0 | Responses with `Set-Cookie`, `Cache-Control: no-store/private`, or a background task are never cached | Cookies and private data could be replayed to other clients | Implemented in `0.3.0a2` |
| 0.3.0 | Injected `response` metadata is checked before cache reads and writes | Dict/list responses could cache cookies, private data, custom statuses, or custom headers | Implemented in `0.3.0a2` |
| 0.3.0 | A second `FastAPICache.init(...)` is not a silent no-op | Configuration was impossible to change | Merged on `stable`; ships in `0.3.0b1` |

## Cache data compatibility

- **ETag:** the value changes once. The new value is a stable SHA-256 digest; clients may
  revalidate after upgrading.
- **Default key format:** the builder implementation and its arguments are unchanged from
  `fastapi-cache2 0.2.2`; matching prefix, namespace, function, arguments and keyword arguments
  continue to address the same ordinary entries. A namespace rotation is not required solely
  because the distribution changes.
- **Error responses:** old cached error entries may remain until their TTL expires. Flush
  the cache namespace if you were affected.
- **Authenticated responses:** entries written by versions that cached authenticated requests
  under the default key may remain. Clear or rotate the cache namespace before deploying the
  bypass, including all instances/workers and persistent Redis caches. The bypass is not
  retroactive.
- **InMemory:** data is process-local and is lost on restart. Instances no longer share a
  store; a new backend after `FastAPICache.reset()` starts empty. No data-format migration.
- **Pydantic/dataclass values:** the default `JsonCoder` decodes cached JSON using its legacy
  behavior; it does not promise to reconstruct the annotated type. Typed restoration is opt-in
  through `TypedJsonCoder` and applies only to its documented supported types. Review coder
  compatibility before reusing entries written with a different coder.
- **Timezone-aware JSON datetimes:** `JsonCoder` round-trips the instant and encoded UTC
  offset, but does not retain the original IANA timezone identifier. Store the zone name
  separately or use a custom coder if later DST-aware arithmetic needs it.
- **`_spec_type`:** the internal marker changed to `__fastapi_cache_spec_type__`. Old entries
  written with `_spec_type` are treated as user data; flush the namespace if you cache
  `datetime`/`date`/`Decimal` values.

## How compatibility is tested

- API signature tests for the public names above.
- Characterization tests for the normal GET success path.
- Auth/privacy tests for default bypass, opt-in isolation, backend non-access, and legacy
  cache-entry invalidation.
- InMemory tests for `expire=None`, instance isolation, clear isolation, and decorator
  default-expire behavior.
- Regression tests for every behavior change.
- Functional CI tests Python 3.10–3.13 with resolver-selected FastAPI and Pydantic versions.
- A separate security-audit profile scans Python 3.11–3.13 with the project extras and
  FastAPI's standard runtime extras; development-only tools are excluded.
- A Pydantic v1 migration-compatibility job remains on Python 3.11 with FastAPI 0.111.1 and
  Pydantic 1.10.27; this does not expand the security-support policy to Pydantic v1.
- Legacy CI tests Python 3.8/3.9 with pinned FastAPI 0.111.1 and Pydantic 1.10.27/2.8.2,
  and smoke-installs the wheel on Python 3.8. Python 3.10 is exercised by the main functional
  matrix and Pydantic v1 compatibility job; none of these EOL profiles is security-supported.
- Wheel and sdist smoke tests in a clean virtual environment.
- Redis 7 integration tests run in CI.
- Memcached and DynamoDB have unit tests with fake clients in CI (`optional-backends` job).
  They cover key encoding, get/set, TTL handling and the unimplemented `clear`. They do not
  use a real service, so both backends stay Experimental.
- Migration tests that install the package and run a small app.

## If we break something

We treat a compatibility break as a bug:

1. Open an issue with the bug report form, or use private vulnerability reporting for a
   vulnerability.
2. Document the break and the rollback path in `MIGRATION.md`.
3. Publish a patch release with a regression test.
4. If the break is unavoidable, announce it before the release and provide a migration path.

## Not covered by this contract

- Private APIs of FastAPI, Starlette or Pydantic.
- Behavior of optional backends marked experimental.
- Undocumented attributes such as `FastAPICache._backend` or `_enable`.
- Exact cache key strings, ETag values, header ordering or log messages.
- Performance characteristics.

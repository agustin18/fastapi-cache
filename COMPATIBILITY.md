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
- Existing `@cache(...)` and `FastAPICache.init(...)` calls keep working without code changes.
- Authenticated requests bypass the cache by default. This is an intentional privacy behavior
  change; authenticated endpoints must opt in with `cache_authenticated=True` and an
  identity-aware `key_builder` to keep caching.
- `InMemoryBackend` instances are isolated: each owns its store and lock. `expire=None` means
  no expiration. InMemory remains process-local; use a shared backend for cross-process
  caching.
- Existing custom backends, coders and key builders that implement the documented protocols
  keep working.
- Migration from `fastapi-cache2` does not require application code changes for valid legacy
  use cases.
- Pydantic v2 users can opt into `TypedJsonCoder` for typed restoration; the default
  `JsonCoder` keeps the legacy decoded behavior. Pydantic v1 and unsupported annotations
  keep the legacy behavior.
- Python 3.8/3.9 legacy compatibility is validated in CI with FastAPI 0.111.1 and
  Pydantic 1.10.27/2.8.2; it is migration compatibility, not a new-production recommendation.

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
classmethod encode(value) -> bytes
classmethod decode(value: bytes) -> Any
classmethod decode_as_type(value: bytes, *, type_) -> Any
```

## Support levels

- **Migration compatibility:** tested legacy combinations are kept so existing applications can
  move to this fork without code changes. This is not a recommendation for new production
  deployments.
- **Security-supported environment:** current Python, FastAPI and Pydantic releases that still
  receive upstream security fixes. This project does not backport security fixes for
  end-of-life upstreams.

Python 3.8, 3.9 and 3.10 are end-of-life, and Pydantic v1 is end-of-life with 1.10.27 as its
final release. They remain in the migration matrix for compatibility, not as supported
security targets.

## Supported matrix for `0.3.x`

> The `0.3.0` line keeps `python = "^3.8"` for legacy migration. Python 3.8/3.9/3.10 and
> Pydantic v1 are end-of-life upstream; they are tested for migration, not recommended for
> new production deployments. The minimum supported Python will be revisited only after the
> compatibility matrix and an explicit floor decision.

Status definitions:

- **Verified**: tested in CI with identified versions.
- **Targeted for 0.3.0**: intended behavior, not yet guaranteed.
- **Experimental**: interface available, coverage insufficient.
- **Unsupported**: outside the compatibility contract.

| Component | Status | Notes |
|---|---|---|
| Python 3.10–3.13 | Verified | CI matrix runs the suite; Python 3.10 is EOL and kept for migration |
| Python 3.8/3.9 | Verified for migration | Legacy CI job with FastAPI 0.111.1 and Pydantic 1.10.27/2.8.2; EOL, not recommended for new production |
| Python 3.14 | Targeted | Evaluated after the first stable release |
| FastAPI | Verified with 0.111.1 and current 0.x | Older 0.100.x validation is a beta gate; no upper pin yet (`fastapi = "*"`) |
| Pydantic 2.x | Verified | Typed restoration is opt-in via `TypedJsonCoder`; default `JsonCoder` keeps legacy behavior |
| Pydantic v1 | Verified for migration | Tested with 1.10.27; EOL, no new security fixes; typed restoration is not applied |
| `Response`/`JSONResponse` annotations | Legacy decoded behavior | No Pydantic schema generation; cache hits keep working |
| Redis standalone | Verified for clear semantics | Redis 7 service in CI with redis-py 4.6.0; key-only clear and namespace boundary tested. redis-py 5/6 are not supported by the current `^4.2.0rc1` constraint and are untested |
| Redis Cluster | Unsupported for namespace clear | Key-only clear is supported; namespace clear raises `NotImplementedError`; no complete namespace clearing |
| InMemory | Verified for basic operations, clear semantics, `expire=None` and instance isolation | Unit tests; each instance owns its store and lock; no size cap yet |
| Memcached | Experimental | No full `clear`/TTL parity; `clear` raises `NotImplementedError` |
| DynamoDB | Experimental | `clear` raises `NotImplementedError`; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

> Redis results in `0.3.0a1` cover Redis 7 with redis-py 4.6.0. Other client or server
> versions are not verified; do not infer support from the Redis 7 job alone.

### `0.3.0a1` status

Implemented: error responses, opt-in `TypedJsonCoder`, `clear()` key/namespace semantics,
Redis Cluster namespace `NotImplementedError`, and the legacy compatibility matrix.

### Unreleased on `stable`

Implemented on `stable` (unreleased; target `0.3.0a2`): authenticated requests bypass the
cache by default; opt-in with `cache_authenticated=True` and an identity-aware `key_builder`.
Opting in with the default key builder raises `ValueError` for authenticated requests.
`InMemoryBackend` instances are isolated, and `expire=None` means no expiration. The
decorator emits `Cache-Control: max-age` only for valid, non-negative expiry values; it
omits `max-age` for `expire=None` and no-expiration hits. `expire=0` keeps the legacy
fallback to the global `expire` value. ETags are quoted weak validators derived from a
stable SHA-256 digest; `If-None-Match` uses weak comparison, supports lists and `*`, is
evaluated on hits and misses, and ignores malformed entity-tags.

Targeted for later pre-releases: non-JSON bypass, `_spec_type` collision handling, explicit
re-`init()`, and the Redis client/server matrix.

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
clear-semantics fixes are implemented in `0.3.0a1`; the auth/privacy bypass is implemented
on `stable` (unreleased; target `0.3.0a2`); the remaining rows are targeted for later
pre-releases. Each one is documented in [`MIGRATION.md`](MIGRATION.md) and covered by a
regression test when implemented.

| Version | Change | Why | Status |
|---|---|---|---|
| 0.3.0 | Error `Response` objects (status >= 400) are not cached | A cached 404 could be returned as 200 | Implemented on `stable` |
| 0.3.0 | Opt-in `TypedJsonCoder` decodes cached JSON into the annotated return type on Pydantic v2 | Default `JsonCoder` and Pydantic v1 keep the legacy decoded behavior; `TypedJsonCoder` propagates validation errors | Implemented on `stable` |
| 0.3.0 | Authenticated requests bypass the cache by default | Prevent cross-user response reuse | Implemented on `stable` (unreleased; target 0.3.0a2) |
| 0.3.0 | ETag is stable across processes and correctly quoted | `hash()` is randomized per process and the old header was invalid | Implemented on `stable` (unreleased; target 0.3.0a2) |
| 0.3.0 | `clear(key=...)` deletes only that key | It used to delete the whole prefix namespace | Implemented on `stable` |
| 0.3.0 | `clear("app:user")` does not delete `app:users` | Namespace matching requires the `:` boundary | Implemented on `stable` |
| 0.3.0 | Redis Cluster namespace clear raises `NotImplementedError` | Partial/unsafe clearing was not reliable | Implemented on `stable` |
| 0.3.0 | `expire=None` means no expiration in `InMemoryBackend` | It used to expire almost immediately | Implemented on `stable` (unreleased; target 0.3.0a2) |
| 0.3.0 | `InMemoryBackend` instances do not share state | The class-level store leaked entries between instances | Implemented on `stable` (unreleased; target 0.3.0a2) |
| 0.3.0 | `Cache-Control` never emits `max-age=None` or `max-age=-1` | Invalid headers | Implemented on `stable` (unreleased; target 0.3.0a2) |
| 0.3.0 | User payloads with a `_spec_type` key are not interpreted as internal metadata | The marker collided with user data | Targeted |
| 0.3.0 | Non-JSON responses (streaming, file, redirect) are not cached blindly | Status/headers/body were lost or corrupted | Targeted |
| 0.3.0 | A second `FastAPICache.init(...)` is not a silent no-op | Configuration was impossible to change | Targeted |

## Cache data compatibility

- **ETag:** the value changes once. The new value is a stable SHA-256 digest; clients may
  revalidate after upgrading.
- **Key format:** if a release changes the default key format, old entries become
  unreachable. Flush the cache namespace after upgrading.
- **Error responses:** old cached error entries may remain until their TTL expires. Flush
  the cache namespace if you were affected.
- **Authenticated responses:** entries written by versions that cached authenticated requests
  under the default key may remain. Clear or rotate the cache namespace before deploying the
  bypass, including all instances/workers and persistent Redis caches. The bypass is not
  retroactive.
- **InMemory:** data is process-local and is lost on restart. Instances no longer share a
  store; a new backend after `FastAPICache.reset()` starts empty. No data-format migration.
- **Pydantic/dataclass values:** old entries encoded as plain JSON still decode; the
  annotated type is restored on read. No flush required for this fix alone.

## How compatibility is tested

- API signature tests for the public names above.
- Characterization tests for the normal GET success path.
- Auth/privacy tests for default bypass, opt-in isolation, backend non-access, and legacy
  cache-entry invalidation.
- InMemory tests for `expire=None`, instance isolation, clear isolation, and decorator
  default-expire behavior.
- Regression tests for every behavior change.
- CI tests Python 3.10–3.13 with resolver-selected FastAPI and Pydantic versions.
- A `legacy-compat` job tests Python 3.8/3.9 with FastAPI 0.111.1 and Pydantic 1.10.27/2.8.2,
  plus Python 3.10/3.11 with Pydantic 1.10.27.
- A `legacy-smoke` job builds the wheel and installs it on Python 3.8 with Pydantic 1.10.27.
- Wheel and sdist smoke tests in a clean virtual environment.
- Redis 7 integration tests run in CI; Memcached and DynamoDB backend integration tests are
  planned.
- Migration tests that install the package and run a small app.

## If we break something

We treat a compatibility break as a bug:

1. Open an issue (when issues are enabled) or a private security advisory for a
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

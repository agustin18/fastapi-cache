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
- Existing custom backends, coders and key builders that implement the documented protocols
  keep working.
- Migration from `fastapi-cache2` does not require application code changes for valid legacy
  use cases.
- Pydantic v2 users can opt into `TypedJsonCoder` for typed restoration; the default
  `JsonCoder` keeps the legacy decoded behavior. Pydantic v1 and unsupported annotations
  keep the legacy behavior.
- Python 3.8/3.9 legacy compatibility is intended; the compatibility matrix will validate it
  before `0.3.0a1`.

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
```

### `@cache(...)`

```python
cache(
    expire=None,
    coder=None,
    key_builder=None,
    namespace="",
    injected_dependency_namespace="__fastapi_cache",
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
| Redis standalone | Targeted | redis-py 5/6; no real Redis integration test yet |
| Redis Cluster | Unsupported | `clear` limitations documented; no complete namespace clearing |
| InMemory | Verified for basic operations | Unit tests; instance isolation is targeted for 0.3.0; the current implementation shares state between instances; no size cap yet |
| Memcached | Experimental | No full `clear`/TTL parity |
| DynamoDB | Experimental | `clear` is not implemented; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

## Intentional behavior changes

These are bug fixes targeted for `0.3.0`. The error-response and typed-decode fixes are
implemented on `stable`; the remaining rows are targeted for later pre-releases. Each one is
documented in [`MIGRATION.md`](MIGRATION.md) and covered by a regression test when implemented.

| Version | Change | Why | Status |
|---|---|---|---|
| 0.3.0 | Error `Response` objects (status >= 400) are not cached | A cached 404 could be returned as 200 | Implemented on `stable` |
| 0.3.0 | Opt-in `TypedJsonCoder` decodes cached JSON into the annotated return type on Pydantic v2 | Default `JsonCoder` and Pydantic v1 keep the legacy decoded behavior; `TypedJsonCoder` propagates validation errors | Implemented on `stable` |
| 0.3.0 | Authenticated requests bypass the cache by default | Prevent cross-user response reuse | Targeted |
| 0.3.0 | ETag is stable across processes and correctly quoted | `hash()` is randomized per process and the old header was invalid | Targeted |
| 0.3.0 | `clear(key=...)` deletes only that key | It used to delete the whole prefix namespace | Targeted |
| 0.3.0 | `clear("app:user")` does not delete `app:users` | Namespace matching requires the `:` boundary | Targeted |
| 0.3.0 | `expire=None` means no expiration in `InMemoryBackend` | It used to expire almost immediately | Targeted |
| 0.3.0 | `Cache-Control` never emits `max-age=None` or `max-age=-1` | Invalid headers | Targeted |
| 0.3.0 | User payloads with a `_spec_type` key are not interpreted as internal metadata | The marker collided with user data | Targeted |
| 0.3.0 | Non-JSON responses (streaming, file, redirect) are not cached blindly | Status/headers/body were lost or corrupted | Targeted |
| 0.3.0 | A second `FastAPICache.init(...)` is not a silent no-op | Configuration was impossible to change | Targeted |

## Cache data compatibility

- **ETag:** the value changes once. Clients may revalidate after upgrading.
- **Key format:** if a release changes the default key format, old entries become
  unreachable. Flush the cache namespace after upgrading.
- **Error responses:** old cached error entries may remain until their TTL expires. Flush
  the cache namespace if you were affected.
- **Pydantic/dataclass values:** old entries encoded as plain JSON still decode; the
  annotated type is restored on read. No flush required for this fix alone.

## How compatibility is tested

- API signature tests for the public names above.
- Characterization tests for the normal GET success path.
- Regression tests for every behavior change.
- CI tests Python 3.10–3.13 with resolver-selected FastAPI and Pydantic versions.
- A `legacy-compat` job tests Python 3.8/3.9 with FastAPI 0.111.1 and Pydantic 1.10.27/2.8.2,
  plus Python 3.10/3.11 with Pydantic 1.10.27.
- A `legacy-smoke` job builds the wheel and installs it on Python 3.8 with Pydantic 1.10.27.
- Wheel and sdist smoke tests in a clean virtual environment.
- Backend integration tests are planned.
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

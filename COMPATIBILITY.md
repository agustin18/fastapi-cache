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

## Public surface

```python
from fastapi_cache import FastAPICache, Backend, Coder, JsonCoder, KeyBuilder, default_key_builder
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

## Supported matrix for `0.3.x`

> The current `0.3.0a0` alpha still carries the inherited `>=3.8` metadata. The `0.3.0`
> release will align `pyproject.toml`, classifiers, tox and CI with the matrix below.

Status definitions:

- **Verified**: tested in CI with identified versions.
- **Targeted for 0.3.0**: intended behavior, not yet guaranteed.
- **Experimental**: interface available, coverage insufficient.
- **Unsupported**: outside the compatibility contract.

| Component | Status | Notes |
|---|---|---|
| Python 3.10–3.13 | Verified | CI matrix runs the suite on each version |
| Python 3.14 | Targeted | Evaluated after the first stable release |
| FastAPI | Targeted | No pinned range yet (`fastapi = "*"`); pin before beta |
| Pydantic 2.x | Targeted | CI installs the latest resolution; minimum version not verified |
| Redis standalone | Targeted | redis-py 5/6; no real Redis integration test yet |
| Redis Cluster | Unsupported | `clear` limitations documented; no complete namespace clearing |
| InMemory | Verified for basic operations | Unit tests; instance isolation is targeted for 0.3.0; the current implementation shares state between instances; no size cap yet |
| Memcached | Experimental | No full `clear`/TTL parity |
| DynamoDB | Experimental | `clear` is not implemented; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |
| Pydantic v1 | Unsupported | Not supported in 0.3.x |
| Python 3.8/3.9 | Unsupported | Metadata still allows them temporarily; no 0.3.x guarantee |

## Intentional behavior changes

These are bug fixes targeted for `0.3.0`. The current alpha does not include all of them.
Each one will be documented in [`MIGRATION.md`](MIGRATION.md) and covered by a regression
test when implemented.

| Version | Change | Why |
|---|---|---|
| 0.3.0 | Error `Response` objects (status >= 400) are not cached | A cached 404 could be returned as 200 |
| 0.3.0 | Authenticated requests bypass the cache by default | Prevent cross-user response reuse |
| 0.3.0 | ETag is stable across processes and correctly quoted | `hash()` is randomized per process and the old header was invalid |
| 0.3.0 | `clear(key=...)` deletes only that key | It used to delete the whole prefix namespace |
| 0.3.0 | `clear("app:user")` does not delete `app:users` | Namespace matching requires the `:` boundary |
| 0.3.0 | `expire=None` means no expiration in `InMemoryBackend` | It used to expire almost immediately |
| 0.3.0 | `Cache-Control` never emits `max-age=None` or `max-age=-1` | Invalid headers |
| 0.3.0 | User payloads with a `_spec_type` key are not interpreted as internal metadata | The marker collided with user data |
| 0.3.0 | Non-JSON responses (streaming, file, redirect) are not cached blindly | Status/headers/body were lost or corrupted |
| 0.3.0 | A second `FastAPICache.init(...)` is not a silent no-op | Configuration was impossible to change |

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
- CI currently tests Python 3.10–3.13 with resolver-selected FastAPI and Pydantic versions.
  Version-specific compatibility matrices and backend integration tests are planned.
- Wheel and sdist smoke tests in a clean virtual environment.
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

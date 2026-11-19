# Compatibility contract

`fastapi-cache-stable` is an independent, community-maintained fork of
[`fastapi-cache2`](https://pypi.org/project/fastapi-cache2/). This document defines what
"drop-in" means for this project and what we promise to keep stable.

This contract describes the documented `0.3.x` line. Use
[PyPI](https://pypi.org/project/fastapi-cache-stable/) and
[CHANGELOG.md](CHANGELOG.md) for current releases and historical versions.

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
- FastAPI return-annotation response-model inference is **opt-in** with
  `@cache(infer_response_model=True)`. The legacy default avoids rejecting
  previously valid routes with non-Pydantic-compatible return annotations,
  such as `Union[Response, dict]`. Opting in also enables output validation.
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
    infer_response_model=False,
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
- **Security-supported environment:** server-side CPython 3.11–3.13 with the resolver-selected
  FastAPI and Pydantic versions, plus the optional dependency profiles included in the security audit.
  Security support means investigating and addressing applicable issues in this documented
  scope; it does not certify every possible downstream dependency combination as vulnerability-free.
- The verified compatibility and security matrices target server-side CPython. Pyodide/browser/Node
  runtimes are not tested or covered by these guarantees; this is a scope statement, not a claim
  that the package is functionally incompatible there. Consumers using urllib3 in those runtimes
  must assess their own redirect behavior.
- **Critical legacy findings:** EOL status alone is not an applicability verdict. Critical
  advisories in legacy profiles must be assessed for package-controlled execution paths,
  mitigations and residual risk before stable.

Python 3.8, 3.9 and 3.10 are end-of-life, and Pydantic v1 is end-of-life with 1.10.27 as its
final release. Stable `0.3.0` retains the package range `>=3.8,<3.14`; Python 3.8–3.10 are
tested for legacy functional compatibility but are not security-supported. Pydantic v1 keeps
its documented legacy decoded behavior, but receives no new upstream security fixes.

### Security and compatibility are different promises

| Python | Functional compatibility with the fork | Security support for `0.3.x` | Known boundary |
|---|---|---|---|
| 3.8–3.9 | Verified legacy matrix, core Redis/InMemory | **No** | Legacy profiles can resolve vulnerable AnyIO 4.5.2 and Starlette 0.44.0 |
| 3.10 | Verified legacy matrix | **No** | EOL interpreter; security fixes depend on the consuming app and compatible dependencies |
| **3.11–3.13** | **Verified** | **Best-effort, recommended** | Verified modern runtime wheel profiles; not a claim about all consumer packages |
| 3.14 | Not verified | No | Not in 0.3.x metadata range |

A legacy Python installation can work correctly and still retain dependency
vulnerabilities. Neither an installation on EOL Python nor a switch from
`fastapi-cache2` **automatically fixes** Starlette, AnyIO, urllib3 or
any unrelated vulnerability. The two distributions may resolve different
dependency graphs; only individual installed versions and reachable code
paths establish exposure. The upstream `redis` optional dependency uses
redis-py 5.x, whereas `0.3.x` of this fork currently verifies redis-py 4.6.0;
projects requiring redis-py 5/6 must not assume a drop-in resolver match.

See [Legacy support and known GHSA](audit/security/LEGACY_SUPPORT_AND_RISKS.md)
and [SECURITY.md](SECURITY.md). **Use Python 3.11–3.13 and patched
compatible dependencies for production**, not EOL interpreters.

## Supported matrix for `0.3.x`

> Stable `0.3.0` metadata is `python = ">=3.8,<3.14"`. Functional compatibility and security
> support are separate: Python 3.8–3.10 are legacy-tested only; security support is Python
> server-side CPython 3.11–3.13. Python 3.14 remains unsupported pending a full matrix.

Status definitions:

- **Verified**: tested in CI with identified versions.
- **Targeted for 0.3.0**: intended behavior, not yet guaranteed.
- **Experimental**: interface available, coverage insufficient.
- **Unsupported**: outside the compatibility contract.

| Component | Status | Notes |
|---|---|---|
| CPython 3.11–3.13 | Security-supported | Full functional and security-audit matrices |
| Python 3.10 | Legacy functional compatibility | Main functional CI plus Pydantic v1 compatibility; EOL, no security-support commitment |
| Python 3.8–3.9 | Legacy functional compatibility | Pinned FastAPI/Pydantic matrix and Python 3.8 wheel smoke; EOL, no security-support commitment |
| Python 3.14 | Unsupported for `0.3.0` | Requires a full CI matrix before support is announced |
| FastAPI | Verified with 0.111.1 and current 0.x | Older 0.100.x is unverified; no upper pin yet (`fastapi = "*"`) |
| Pydantic 2.x | Verified | Typed restoration is opt-in via `TypedJsonCoder`; default `JsonCoder` keeps legacy behavior |
| Pydantic v1 | Verified for migration | Tested with 1.10.27; EOL, no new security fixes; typed restoration is not applied |
| `Response`/`JSONResponse` annotations | Legacy decoded behavior | No Pydantic schema generation; cache hits keep working |
| Redis standalone | Verified for clear semantics | Redis 7 service in CI with redis-py 4.6.0; key-only clear and namespace boundary tested. redis-py 5/6 are not supported by the current `^4.2.0rc1` constraint and are untested |
| Redis Cluster | Unsupported for namespace clear | Key-only clear is supported; namespace clear raises `NotImplementedError`; no complete namespace clearing |
| InMemory | Verified for basic operations, clear semantics, `expire=None` and instance isolation | Unit tests; each instance owns its store and lock; no size cap yet |
| Memcached | Experimental | Unit tests with a fake client; `get_with_ttl` returns a fixed `3600` instead of the real remaining time; `clear` raises `NotImplementedError` |
| DynamoDB | Experimental; Python >=3.10 only for target `0.3.0` | `dynamodb` extra requires aiobotocore and aiohttp >=3.14.4; the extra omits those dependencies on Python 3.8/3.9. Unit tests use a fake client; `clear` raises `NotImplementedError`; no real-service integration |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

> Verified Redis integration covers Redis 7 with redis-py 4.6.0. Other
> versions are not verified by that job alone.

### Implemented behavior

The current maintained line includes error-response bypass, optional Pydantic v2
typed decoding, narrow invalidation, authenticated-request bypass, isolated
InMemory stores, corrected Cache-Control and ETags, safe response-type handling
and an explicit second-initialization contract. For precise behavioral
differences see [MIGRATION.md](MIGRATION.md); for introduction versions see
[CHANGELOG.md](CHANGELOG.md).

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

The following compatibility-affecting fixes have regression coverage.
Historical introduction versions belong in [CHANGELOG.md](CHANGELOG.md).

| Change | Why it matters |
|---|---|
| Error `Response` objects (status >= 400) are not cached | A cached 404 could be returned as 200 |
| Opt-in `TypedJsonCoder` decodes cached JSON into the annotated return type on Pydantic v2 | Default `JsonCoder` and Pydantic v1 keep the legacy decoded behavior; `TypedJsonCoder` propagates validation errors |
| Authenticated requests bypass the cache by default | Prevent cross-user response reuse |
| ETag is stable across processes and correctly quoted | `hash()` is randomized per process and the old header was invalid |
| `clear(key=...)` deletes only that key | It used to delete the whole prefix namespace |
| `clear("app:user")` does not delete `app:users` | Namespace matching requires the `:` boundary |
| Redis Cluster namespace clear raises `NotImplementedError` | Partial/unsafe clearing was not reliable |
| `expire=None` means no expiration in `InMemoryBackend` | It used to expire almost immediately |
| `InMemoryBackend` instances do not share state | The class-level store leaked entries between instances |
| `Cache-Control` never emits `max-age=None` or `max-age=-1` | Invalid headers |
| User payloads with a `_spec_type` key are not interpreted as internal metadata | The marker collided with user data |
| Only simple `JSONResponse` objects are cached by `JsonCoder`; other responses bypass | Status/headers/body were lost or corrupted |
| Responses with `Set-Cookie`, `Cache-Control: no-store/private`, or a background task are never cached | Cookies and private data could be replayed to other clients |
| Injected `response` metadata is checked before cache reads and writes | Dict/list responses could cache cookies, private data, custom statuses, or custom headers |
| A second `FastAPICache.init(...)` is not a silent no-op | Configuration was impossible to change |

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

## Drop-in limits and inherited integration gaps

For GET/JSON with standalone Redis or InMemory and the documented default
key builder, normal imports and signatures remain. That is not universal
byte-for-byte behavior compatibility:

- Authenticated `Authorization`/`Cookie` requests now bypass the cache;
  legacy private entries may need selective invalidation.
- Repeated `init()` now raises; `clear(key=...)` no longer has legacy
  broad namespace effects.
- The original key builder still hashes `repr(args)`/`repr(kwargs)`.
  Injected session objects whose representations change can prevent cache
  hits. The upstream [`exclude_params` PR #574](https://github.com/long2ice/fastapi-cache/pull/574)
  is not implemented. Do not remove identity-sensitive fields from keys.
- `fastapi-pagination` integration remains unverified
  ([upstream issue #557](https://github.com/long2ice/fastapi-cache/issues/557)).
  Complete OpenAPI/`response_model` parity remains out of scope
  ([upstream issue #384](https://github.com/long2ice/fastapi-cache/issues/384)).
- redis-py 5/6, complete Redis Cluster namespace clear and production parity
  for experimental Memcached/DynamoDB are not guaranteed.

These are support boundaries, not assertions that every combination fails.
See [application verification](MIGRATION.md#application-verification-before-traffic).

## Not covered by this contract

- Private APIs of FastAPI, Starlette or Pydantic.
- Behavior of optional backends marked experimental.
- Undocumented attributes such as `FastAPICache._backend` or `_enable`.
- Exact cache key strings, ETag values, header ordering or log messages.
- Performance characteristics.

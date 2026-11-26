# Compatibility contract

`fastapi-cache-stable` is an independent, community-maintained fork of
[`fastapi-cache2`](https://pypi.org/project/fastapi-cache2/). This document defines what
"drop-in" means for this project and what we promise to keep stable.

This contract describes the published `0.8.0` release and the retained
`0.4.x` compatibility behavior. Inspect the installed distribution and its
source provenance; a source checkout alone is not publication evidence. The
`0.3.x` artifacts remain an earlier migration line. Use
[PyPI](https://pypi.org/project/fastapi-cache-stable/) and
[CHANGELOG.md](CHANGELOG.md) for current releases and historical versions.

## 0.8.0 compatibility

The published 0.8.0 package retains `Requires-Python >=3.8,<3.15`, documented
Python-conditional Redis client bounds, imports and ordinary default keys.
It keeps optional bounded InMemory and the 0.6.0 privacy corrections, and adds
inclusive InMemory TTL expiry, decode-before-304 validation and the documented
Redis `get_with_ttl()` tuple. Final release artifact verification is recorded in
[RELEASE_STATUS_0.8.0.md](docs/releases/RELEASE_STATUS_0.8.0.md) with the
annotated tag, wheel/sdist SHA-256 and successful Phase B/TestPyPI/PyPI runs.
The matrix below describes the published 0.8.0 contract; no backend or Python
version beyond this release is qualified.

## 0.8.0 Python 3.14 qualification

The diagnostic [Python 3.14 qualification](docs/audit/PYTHON_3_14_QUALIFICATION.md)
passed on standard CPython 3.14.10 with real Redis 7.4 and installed security
profiles. The 0.8.0 release retains the 0.7.2 standard CPython 3.14 qualification;
the security target is server-side CPython 3.11–3.14, subject to the
exact-artifact evidence in the release status. Python 3.8–3.10 remain
functional legacy only. Memcached/DynamoDB remain experimental; fake-client
tests do not establish service conformance. Free-threaded 3.14t and 3.15 are
outside this release. The tables below describe the published 0.8.0 contract.

## 0.6.0 compatibility (historical)

The 0.6.0 package introduced optional bounded InMemory and targeted private
HTTP response corrections. Its immutable record remains in
[RELEASE_STATUS_0.6.0.md](docs/releases/RELEASE_STATUS_0.6.0.md).

## Redis client support in 0.8.0

Published `0.8.0` inherits the `0.6.0`/`0.4.0` Redis support and incorporates the #47 implementation, changing
only the optional Redis client requirements and verification matrix, not
the RedisBackend runtime semantics. The previous `0.3.x` release declared
redis-py 4.x only.

| CPython | redis-py versions | Constraint |
|---|---|---|
| 3.8 | redis-py 4.x, 5.x, 6.0–6.1 | `>=4.2.0rc1,<6.2` |
| 3.9 | redis-py 4.x, 5.x, 6.x, 7.0 | `>=4.2.0rc1,<7.1` |
| 3.10–3.14 | redis-py 4.x–8.1.x | `>=4.2.0rc1,<8.2` |

These ranges deliberately retain legacy client 4.x and cap every range
before the first untested/incompatible minor. They are **not** evidence of
unbounded compatibility with future client releases. This release targets standalone Redis with RESP2/RESP3, ACL and binary caching using
`decode_responses=False`; Cluster namespace clear remains unsupported and
TLS/Sentinel/Cluster/failover certification remains out of scope.

The investigation is recorded in
[audit/redis/REDIS_CLIENT_MATRIX_RESEARCH.md](audit/redis/REDIS_CLIENT_MATRIX_RESEARCH.md),
and the implementation PR runs a smaller mandatory wheel/sdist CI matrix.
Existing `0.3.x` PyPI artifacts remain immutable. The expanded contract
applies to the published `0.8.0` artifact.

## Factory-generated HTTP handlers (#68, fixed in published 0.4.1)

**Published 0.4.0 is affected; published 0.4.1 fixes the generated/wrapped
HTTP handler collision**: factory-created functions can share
module/name/args/namespace while serving different HTTP routes. This can
cause a wrong response to be replayed in 0.4.0. Upgrade to 0.4.1 or
choose separate route namespaces / a reviewed path-aware builder.
See [#68](https://github.com/agustin18/fastapi-cache/issues/68).

The shipped narrow fix separates **generated/wrapped HTTP handler
cache keys** by stable request method/host/root/path and the legacy digest.
It detects actual function **closures via code free variables** and
explicit decorator wrappers via `__wrapped__`, even when
`functools.wraps` has copied module-level `__name__`/`__qualname__`
metadata. This covers factory values bound as **default arguments**,
which have no code free variables. Local functions and lambdas are also
detected. Checking `__wrapped__` directly is sufficient here; recursively
calling `inspect.unwrap` is unnecessary and would add work/possible wrapper
chain errors per request.

The exported `default_key_builder` and **unwrapped module-level** handler
keys remain unchanged. Any module-level handler decorated by another
function that sets `__wrapped__`, even when it is not a closure or factory,
can intentionally receive a new scoped key; review cache warm-up and old
entry TTLs before deploying. Previously shared
generated/wrapped entries are intentionally not reused.

HTTP `Host` is included, normalized **only for ASCII casing**:
`EXAMPLE.TEST` and `example.test` share an entry, while distinct hosts,
ports or spellings can cause different keys. Unrestricted client-supplied
`Host` values can create unbounded cache entries; configure
`TrustedHostMiddleware`/equivalent host validation at the edge. This is
not an authorization check or a tenant boundary. Hidden request context,
custom key builders and independent applications sharing a backend
prefix remain separate responsibilities (#53). Direct non-ASGI `@cache`
usage retains the legacy key behavior. The #68 correction is already
published in 0.4.1; independent application/tenant isolation remains
outside its guarantee.

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
- Stable `0.8.0` keeps functional compatibility for Python 3.8–3.10 through a pinned legacy
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
    vary_headers=None,  # opt-in Sequence[str], introduced in 0.5.0
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

- **Legacy functional compatibility:** stable `0.4.1` installs on Python 3.8–3.10 and tests
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
final release. Stable `0.8.0` retains the package range `>=3.8,<3.15`; Python 3.8–3.10 are
tested for legacy functional compatibility but are not security-supported. Pydantic v1 keeps
its documented legacy decoded behavior, but receives no new upstream security fixes.

### Security and compatibility are different promises

| Python | Functional compatibility with the fork | Security support for `0.7.x` | Known boundary |
|---|---|---|---|
| 3.8–3.9 | Verified legacy matrix, core Redis/InMemory | **No** | Legacy profiles can resolve vulnerable AnyIO 4.5.2 and Starlette 0.44.0 |
| 3.10 | Verified legacy matrix | **No** | EOL interpreter; security fixes depend on the consuming app and compatible dependencies |
| **3.11–3.14** | **Verified** | **Best-effort, recommended** | Verified modern runtime wheel profiles; not a claim about all consumer packages |
| 3.14 | **Verified** | **Best-effort, recommended** | Standard CPython 3.14; exact-artifact Phase B and installed security profiles passed |

A legacy Python installation can work correctly and still retain dependency
vulnerabilities. Neither an installation on EOL Python nor a switch from
`fastapi-cache2` **automatically fixes** Starlette, AnyIO, urllib3 or
any unrelated vulnerability. The two distributions may resolve different
dependency graphs; only individual installed versions and reachable code
paths establish exposure. The **released** upstream `fastapi-cache2==0.2.2` and this fork
both declare `redis ^4.2.0rc1` (redis-py 4.x), and this fork verifies
redis-py 4.6.0. Upstream `main` was later updated to `redis ^5.0.8`, but
those source changes do not constitute published compatibility beyond their release notes.
Projects requiring redis-py 5/6 must not assume they are supported yet.

See [Legacy support and known GHSA](audit/security/LEGACY_SUPPORT_AND_RISKS.md)
and [SECURITY.md](SECURITY.md). **Use Python 3.11–3.14 and patched
compatible dependencies for production**, not EOL interpreters.

## Supported matrix for `0.8.0`

> Stable `0.8.0` metadata is `python = ">=3.8,<3.15"`. Functional compatibility and security
> support are separate: Python 3.8–3.10 are legacy-tested only; security support is Python
> server-side CPython 3.11–3.14. Python 3.14 is supported by 0.8.0.

Status definitions:

- **Verified**: tested in CI with identified versions.
- **Targeted for a future release**: proposed behavior; not yet shipped or guaranteed.
- **Experimental**: interface available, coverage insufficient.
- **Unsupported**: outside the compatibility contract.

| Component | Status | Notes |
|---|---|---|
| CPython 3.11–3.14 | Security-supported | Full functional and security-audit matrices |
| Python 3.10 | Legacy functional compatibility | Main functional CI plus Pydantic v1 compatibility; EOL, no security-support commitment |
| Python 3.8–3.9 | Legacy functional compatibility | Pinned FastAPI/Pydantic matrix and Python 3.8 wheel smoke; EOL, no security-support commitment |
| Python 3.14 | Supported for `0.8.0` | Standard CPython 3.14; exact-artifact Phase B and installed security profiles passed |
| FastAPI | Verified with 0.111.1 and current 0.x | Older 0.100.x is unverified; no upper pin yet (`fastapi = "*"`) |
| Pydantic 2.x | Verified | Typed restoration is opt-in via `TypedJsonCoder`; default `JsonCoder` keeps legacy behavior |
| Pydantic v1 | Verified for migration | Tested with 1.10.27; EOL, no new security fixes; typed restoration is not applied |
| `Response`/`JSONResponse` annotations | Legacy decoded behavior | No Pydantic schema generation; cache hits keep working |
| Redis standalone | Verified for conditional client ranges | Redis 6.2/7.0/7.4/8.0 services; redis-py 4.6.0, 5.2.1, 6.1.x, 7.0.1/7.2.1 and 8.1.0 across the Python-conditional matrix; key-only clear and namespace boundary tested. TLS/Sentinel/Cluster/failover not certified |
| Redis Cluster | Unsupported for namespace clear | Key-only clear is supported; namespace clear raises `NotImplementedError`; no complete namespace clearing |
| InMemory | Verified for basic operations, clear semantics, `expire=None`, instance isolation and opt-in bounded capacity | Published 0.8.0 `max_entries` fixes a **per-instance entry count**, not memory bytes; unbounded remains the default |
| Memcached | Experimental | Unit tests with a fake client; `get_with_ttl` returns a fixed `3600` instead of the real remaining time; `clear` raises `NotImplementedError` |
| DynamoDB | Experimental; Python >=3.10 only for published `0.8.0` | `dynamodb` extra requires aiobotocore and aiohttp >=3.14.4; the extra omits those dependencies on Python 3.8/3.9. Unit tests use a fake client; `clear` raises `NotImplementedError`; no real-service integration |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

### Exact InMemory TTL boundary in published 0.8.0

Published 0.8.0 evaluates the integer-second deadline using
`ttl_ts <= int(time.time())`, so a value is expired at the exact deadline.
`expire=0` and negative InMemory TTLs are expired immediately; Redis rejects
nonpositive EX values. This is an inclusive expiry boundary, not a claim of
monotonic elapsed time: because it uses the wall clock, backward clock changes
can increase the remaining TTL of a still-live entry. Choose and test a
backend for your actual freshness and clock-skew contract.

### Bounded InMemory in published 0.8.0

`InMemoryBackend(max_entries: Optional[int] = None)` is available in
published 0.8.0. The published 0.5.0 backend remains unbounded.

- `None` retains unbounded legacy behavior in 0.8.0. A positive integer caps
  **entry count per instance**, not payload bytes or total cache capacity
  across processes. `bool`, zero, negative and non-integer values fail
  construction validation.
- `max_entries` is a **read-only** property fixed at initialization.
  Assignments raise `AttributeError`; dynamic resizing is unsupported.
- At capacity, a new key reclaims one expired key first if available,
  otherwise the least-recently-used entry. The indexed TTL heap avoids
  a full scan on normal writes. Explicit namespace clearing still scans
  stored keys while holding the instance async lock; for N stored entries
  and k matches the bound is O(N + k log N).
- There is no background sweeper, bytes-based cap or thread/cross-event-loop
  sharing guarantee. Existing cache privacy/tenant boundaries remain
  application responsibilities. This feature **is available** in published
  `fastapi-cache-stable==0.8.0` (introduced in 0.6.0; absent from 0.5.0).
- The cap is per instance and counts entries, not bytes or workers.

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

## Explicit HTTP header variants (introduced in 0.5.0, not in 0.4.1)

The optional `vary_headers` decorator argument isolates only explicitly
declared, validated HTTP request field names; it does not infer hidden state.
Non-opted-in routes retain the original key format. Opted-in keys use the
versioned `prefix:namespace:vary-v1:` space and hash the entire ordered
header-value vector. Missing and empty headers are intentionally distinct.
A `Vary` HTTP response header on its own has **no automatic effect** on
internal key selection. On cacheable returned `Response` values, generated
`Vary` and cache metadata must appear on the **actual returned object**
on MISS/HIT, not just the injected response; 304 also preserves `Vary`.
`JsonCoder` checks a plain `JSONResponse` for eligibility before adding
generated metadata. Returned `Response` values can use `PickleCoder`
when compatible with their other response metadata.

Explicit `Request` routes still bypass the default builder even if
`vary_headers` is supplied. Authenticated caching continues to require
a reviewed identity-aware custom key builder. Any undeclared variation,
including middleware/contextvar/tenant data, is the application's
responsibility. The only credential-related names explicitly rejected
from `vary_headers` are `Authorization`, `Cookie`, and
`Proxy-Authorization`; `X-API-Key` and similar custom fields are not
recognized as authenticated identity. Raw client-controlled values can
multiply backend entries: use validated header domains, rate limits,
capacity limits/eviction and TTLs. Hashed key components do **not**
authenticate tenants or prevent cache flooding. Deploy using deliberate
namespace rotation or cleanup of historical entries; do not conflate
key isolation with deletion.

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
- Candidate functional CI tests Python 3.10–3.14 with resolver-selected FastAPI and Pydantic versions.
- Candidate security-audit profiles scan Python 3.11–3.14 with the project extras and
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

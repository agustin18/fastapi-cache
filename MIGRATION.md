# Migrating from fastapi-cache2

`fastapi-cache-stable` is an independent, community-maintained fork of
[`fastapi-cache2`](https://pypi.org/project/fastapi-cache2/). The Python import is unchanged:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
```

The goal is a drop-in replacement for the common case: same import, same public API, same
normal success-path behavior. Bug fixes that change edge-case behavior are listed below and
are covered by regression tests. See [`COMPATIBILITY.md`](COMPATIBILITY.md) for the full
contract.

> **Status:** this guide describes the published `0.3.0b1` artifact and the target `0.3.0`
> stable behavior. Stable `0.3.0` installs on Python `>=3.8,<3.14`; functional compatibility
> for Python 3.8–3.10 is legacy-only, while security support is Python 3.11–3.13. `0.3.0b1`
> keeps every behavior from `0.3.0a2` and adds an explicit second-`init()` contract: a second
> `FastAPICache.init()` call raises `RuntimeError` unless you pass `force=True`. Call it once
> at application startup (for example in the FastAPI `lifespan`), or call
> `FastAPICache.reset()` before reconfiguring. See
> [Second `init()` call](#second-init-call). Check the installed version before relying on a
> behavior listed here.

## Who should migrate

- You use `fastapi-cache2` 0.2.2 and run stable `0.3.0` on Python 3.8–3.13.
- Python 3.8–3.10 remain legacy functional-compatibility targets. They are EOL and do not
  receive a stable security-support commitment; Python 3.11–3.13 form the security-supported
  matrix.
- You use `InMemoryBackend` or `RedisBackend` (standalone Redis).
- Your endpoints are GET and return JSON, Pydantic models, dataclasses or standard types.
- You need a maintained package without changing the `fastapi_cache` import.

Python 3.8/3.9/3.10 and Pydantic v1 are end-of-life upstream. Stable `0.3.0` preserves tested
functional compatibility for the documented Python 3.8–3.10 combinations, but those EOL
profiles receive no security-support promise. Any critical advisory still requires an
applicability assessment; EOL status alone does not close it. A critical advisory applicable to
package-controlled behavior must be mitigated; application-selected paths require a documented
trigger, residual risk and explicit maintainer acceptance.

The default `JsonCoder` keeps the legacy decoded behavior. Pydantic v2 users can opt into
typed restoration with `TypedJsonCoder`; Pydantic v1 users keep the legacy behavior, so
migration does not require a Pydantic upgrade or application changes.

```python
from fastapi_cache import FastAPICache
from fastapi_cache.coder import TypedJsonCoder

FastAPICache.init(backend, coder=TypedJsonCoder)
```

You can also enable it per endpoint with `@cache(coder=TypedJsonCoder)`.

`TypedJsonCoder` validates cached data and propagates validation errors. It only falls back
for Pydantic v1 models and annotations that cannot be represented by a Pydantic v2 schema.

## Who should not migrate yet

- You need full Memcached or DynamoDB parity. They are experimental in `0.3.x`.
- You use Redis Cluster and need complete namespace clearing.
- You need typed restoration on Pydantic v1; the legacy decoded behavior is preserved instead.
  Pydantic v1 is end-of-life; plan an upgrade to Pydantic v2 for typed restoration and
  security fixes.
- You need tags, stale-while-revalidate, stampede protection or POST caching.
- You need perfect OpenAPI/`response_model` behavior or `fastapi-pagination`.

## Install

`0.3.0b1` is a pre-release. Install the exact version:

```sh
pip uninstall -y fastapi-cache2
pip install "fastapi-cache-stable==0.3.0b1"
# with extras:
pip install "fastapi-cache-stable[redis]==0.3.0b1"
```

Do **not** install both distributions in the same environment: they provide the same
`fastapi_cache` files. `pip check` may still pass because their distribution names and declared
dependencies do not conflict; uninstalling `fastapi-cache2` after installing the fork can remove
the shared import files. Always uninstall the old distribution first, then install and verify the
fork in the same environment.

Verify:

```sh
python -c "import fastapi_cache; print(fastapi_cache.__version__)"
python -c "from fastapi_cache import FastAPICache; print('ok')"
```

### Pre-release installation from TestPyPI

Pre-releases are published to TestPyPI and PyPI. TestPyPI is a separate index and may not
have all dependencies. To verify the exact artifact uploaded to TestPyPI, download it from
that index and install the local wheel:

```sh
python -m pip download --no-deps --only-binary=:all: \
  --index-url https://test.pypi.org/simple/ \
  -d testpypi-dist \
  "fastapi-cache-stable==0.3.0b1"

python -m pip install testpypi-dist/*.whl
python -m pip check
python -c "import fastapi_cache; print(fastapi_cache.__version__)"
```

Dependencies are resolved from PyPI by the normal install of the wheel. TestPyPI is for
validating the distribution, not for production. After that verification, the same version is
published separately to PyPI.

## Compatibility matrix

- **Verified**: tested in CI with identified versions.
- **Targeted for 0.3.0**: intended behavior, not yet guaranteed.
- **Experimental**: interface available, coverage insufficient.
- **Unsupported**: outside the compatibility contract.

| Component | Status | Notes |
|---|---|---|
| Python 3.11–3.13 | Verified, security-supported | Main functional matrix and separate runtime security-audit profile |
| Python 3.10 | Verified legacy compatibility | Main functional tests and Pydantic v1 migration job; EOL, no security-support commitment |
| Python 3.8/3.9 | Verified legacy compatibility | Pinned FastAPI 0.111.1/Pydantic 1.10.27/2.8.2 matrix and wheel smoke; EOL, no security-support commitment |
| Python 3.14 | Unsupported for stable `0.3.0` | Add and pass a full matrix before announcing support |
| FastAPI | Verified with 0.111.1 and current 0.x | Older 0.100.x validation is a beta gate; no upper pin yet (`fastapi = "*"`) |
| Pydantic 2.x | Verified | Typed restoration is opt-in via `TypedJsonCoder`; default `JsonCoder` keeps legacy behavior |
| Pydantic v1 | Verified for migration | Tested with 1.10.27; EOL, no new security fixes; typed restoration is not applied |
| `Response`/`JSONResponse` annotations | Legacy decoded behavior | No Pydantic schema generation; cache hits keep working |
| Redis standalone | Verified for clear semantics | Redis 7 service in CI with redis-py 4.6.0; key-only clear and namespace boundary tested. redis-py 5/6 are not supported by the current `^4.2.0rc1` constraint and are untested |
| Redis Cluster | Unsupported | `clear` limitations documented; no complete namespace clearing |
| InMemory | Verified for basic operations, clear semantics, `expire=None` and instance isolation | Unit tests; each instance owns its store and lock; no size cap yet |
| Memcached | Experimental | No full `clear`/TTL parity |
| DynamoDB | Experimental | `clear` is not implemented; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

> The Redis integration job installs the resolver-selected `redis` version from the project
> constraint (`^4.2.0rc1`), currently 4.6.0, and runs against a Redis 7 service. Other client
> or server versions are not verified in `0.3.0b1`.

## Behavior changes in 0.3.0

These are intentional bug fixes targeted for `0.3.0`. `0.3.0a1` implements the error-response,
typed-decode and clear-semantics fixes; `0.3.0a2` implements the auth/privacy bypass, the
InMemory, `Cache-Control`, ETag, `_spec_type` and non-JSON fixes; `0.3.0b1` implements the
explicit second-`init()` contract. Each one has a regression test and is listed here so you
can decide whether it affects you.

| Change | Before (0.2.2) | After (0.3.0) | Status |
|---|---|---|---|
| Error responses | A cached 404 could be returned as 200 | Responses with status >= 400 are not cached | Implemented in 0.3.0a1 |
| Typed JSON decode | Cache hits returned plain dicts/lists | Opt-in `TypedJsonCoder` on Pydantic v2; default `JsonCoder`, Pydantic v1 and unsupported annotations keep the legacy decoded behavior; validation errors propagate | Implemented in 0.3.0a1 |
| Authenticated requests | Two users could share a cache key | Requests with a non-empty `Authorization` or `Cookie` header bypass the cache by default; other authentication/session mechanisms are not detected automatically. Opt in with `cache_authenticated=True` and a safe `key_builder` | Implemented in 0.3.0a2 |
| ETag | `hash()` changes per process; header unquoted | Stable SHA-256 digest, quoted weak ETag, weak `If-None-Match` comparison including lists and `*` | Implemented in 0.3.0a2 |
| `clear(key=...)` | Deleted the whole prefix namespace | Deletes only that key; pass the full key | Implemented in 0.3.0a1 |
| Namespace boundary | `clear("app:user")` also deleted `app:users` | Requires the `:` boundary | Implemented in 0.3.0a1 |
| Redis Cluster namespace clear | Partial/unsafe clearing | Raises `NotImplementedError`; use key-only clear or flush out of band | Implemented in 0.3.0a1 |
| `expire=None` in InMemory | Expired almost immediately | Means no expiration; `get_with_ttl` returns `-1` | Implemented in 0.3.0a2 |
| `Cache-Control` | Could emit `max-age=None` or `max-age=-1` | Only valid values; `max-age` is omitted when no valid expiry exists | Implemented in 0.3.0a2 |
| `_spec_type` | User payloads with that key raised `TypeError` | Internal marker is namespaced as `__fastapi_cache_spec_type__`; user data is preserved | Implemented in 0.3.0a2 |
| Response caching | Streaming/file/redirect and metadata-bearing `JSONResponse` could be cached incorrectly | `JsonCoder` caches only simple `200`/`application/json` `JSONResponse`; other responses bypass; `PickleCoder` bypasses streaming/file/template; `Set-Cookie`, `Cache-Control: no-store/private` and background tasks never cache | Implemented in 0.3.0a2 |
| Second `init` | Silent no-op | Reconfiguration is explicit: `reset()` or `force=True` | Implemented in 0.3.0b1 |

The error-response, typed-decode and clear-semantics fixes are implemented in `0.3.0a1`.
The auth/privacy bypass, InMemory, `Cache-Control`, ETag, `_spec_type` and non-JSON fixes are
implemented in `0.3.0a2`. The second-`init` fix is implemented in `0.3.0b1`; no alpha
contains it.

### Authenticated requests

`0.3.0a1` caches requests with `Authorization`/`Cookie` using the default key. `0.3.0a2`
bypasses the cache for requests with a non-empty
`Authorization` or `Cookie` header. Public requests keep caching. Functions decorated
without a `Request` parameter have no HTTP identity context and keep using the cache.

To cache authenticated responses, opt in explicitly and provide a key builder that includes
the identity. The key builder must include every dimension that affects the response: token,
session, tenant, permissions, and any other validated principal state. Prefer the principal
your application already validated over raw headers. Do not put credentials in plaintext in
keys or logs; use HMAC-SHA256 with an application secret.

```python
import hashlib
import hmac
import os

from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

CACHE_KEY_SECRET = os.environ["CACHE_KEY_SECRET"].encode()


def identity_key_builder(
    func,
    namespace: str = "",
    *,
    request=None,
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
async def me(request):
    ...
```

If `cache_authenticated=True` is used with the default key builder, an authenticated request
raises `ValueError` before the cache is accessed. A custom key builder alone does not opt in;
the explicit flag is required.

The automatic bypass only detects `Authorization` and `Cookie`. Applications that use
`X-API-Key`, proxy-injected headers, `request.state`, or internal dependencies must review
their cache strategy. `cache_authenticated=True` does not make an unsafe key builder safe.
Every non-empty cookie bypasses caching by default, including anonymous analytics, consent or
preference cookies. This is intentionally conservative and can reduce cache hits on public pages.
Do not ignore a cookie in a custom key builder unless it cannot affect the response.

This fix protects the application cache. It does not configure CDN, reverse-proxy, or browser
caching.

**Action required when upgrading from `0.3.0a1` or earlier:** entries written for
authenticated requests may remain under the old default key. The bypass only affects new
requests. Before deploying, clear or rotate the cache namespace, including all
instances/workers and persistent Redis caches. A public request could otherwise read an old
private entry.

### InMemory expiration and isolation

In `0.3.0a1`, `expire=None` expires almost immediately, and `_store`/`_lock` are shared across
all `InMemoryBackend` instances. In `0.3.0a2`:

- `expire=None` means no expiration; `get_with_ttl` returns `-1`, matching Redis/DynamoDB.
- Each backend instance owns its store and lock. A new backend after `FastAPICache.reset()`
  starts empty. Do not share one instance across event loops or threads; use one instance per
  loop/thread. Subclasses that override `__init__()` must call `super().__init__()`.
- `expire=0` keeps the legacy `or` fallback: it uses the global `expire` value. It is not
  a new "no expiration" or "expire immediately" switch.
- `FastAPICache.reset()` resets configuration, not cache data.
- InMemory remains process-local; use Redis/Memcached for cross-process sharing.

The decorator now omits `max-age` when the effective expiry is unknown (`expire=None`) or
negative, including no-expiration InMemory hits (`ttl=-1`). `ETag` and the cache-status
header are still emitted. This is implemented in `0.3.0a2`.

No data-format migration is needed: InMemory data is process-local and is lost on restart.
If you relied on class-level sharing between instances, use a shared backend instead.

### ETag and conditional requests

ETags are quoted weak validators derived from a stable SHA-256 digest of the cached
representation: `W/"<hex>"`. The value is stable across worker processes. `If-None-Match`
uses weak comparison, so `W/"<digest>"` and `"<digest>"` both match; comma-separated lists
and `*` are supported. Conditional requests are evaluated against the generated
representation on both cache hits and misses, including after `Cache-Control: no-cache`.
Malformed entity-tags are ignored. A matching conditional GET returns `304 Not Modified`
with the ETag and cache-status headers and no body. The ETag value changes once when
upgrading from `0.3.0a1`/0.2.2 because the format changed; clients revalidate and receive
the new value.

The default key-builder implementation and its argument shape are unchanged from
`fastapi-cache2 0.2.2`; matching prefix, namespace, function and arguments continue to address
the same ordinary entries. The ETag format change does not require flushing backend data.

### `_spec_type` and user payloads

The internal marker is now `__fastapi_cache_spec_type__` instead of `_spec_type`. User
payloads that contain `_spec_type` are preserved as normal data. The decoder only interprets
the namespaced marker when the object contains exactly the marker and `val`; any other shape
is returned unchanged. Old cached entries written with the `_spec_type` marker are no longer
converted to `datetime`/`date`/`Decimal`; flush the cache namespace if you rely on those
conversions.

### Non-JSON responses

`JsonCoder` only caches simple `JSONResponse` objects: status `200`, media type
`application/json`, no custom headers, and no background task. `StreamingResponse`,
`FileResponse`, `RedirectResponse`, plain `Response`, template responses, and `JSONResponse`
objects with additional status/header metadata are returned directly and are not cached.
Custom coders can override `Coder.can_encode()` to opt in; `PickleCoder` caches
`JSONResponse`, plain `Response`, and `RedirectResponse` objects, and bypasses streaming,
file, and template responses. Responses with `Set-Cookie`, `Cache-Control: no-store` or
`Cache-Control: private`, or a background task are never cached, regardless of the coder.
A plain `Response` with a JSON media type is bypassed unless it is a `JSONResponse` or a
custom coder supports it. The injected `response` object is checked before a cache read and
before a write; `Set-Cookie`, `Cache-Control: no-store`/`private`, a background task, a
non-`200` status, or any header other than the automatic `content-length` bypasses the cache
for dict/list returns.

**Action required:** if you were affected by cached error responses or by `clear(key=...)`,
flush the cache namespace after upgrading. If you relied on `clear(key=...)` clearing the whole
prefix, switch to `clear()` or `clear(namespace=...)`. If you relied on `clear("app:user")`
deleting `app:users`, use the exact namespace. Redis Cluster users must use key-only clear or
flush the database out of band. Namespace clear is best-effort and not atomic. `clear()` is an
administrative operation; do not expose it to untrusted input. If the ETag changes, clients may
revalidate once. If you previously cached responses with cookies or private data, flush the
namespace as well.

### Second `init()` call

In `0.3.0a1` and `0.3.0a2`, a second `FastAPICache.init()` was a silent no-op: the first
configuration stayed active and the new arguments were ignored. In `0.3.0b1` a second call
raises `RuntimeError`.

```python
FastAPICache.init(InMemoryBackend(), prefix="first")

# Raises RuntimeError: init() was already called
FastAPICache.init(InMemoryBackend(), prefix="second")

# Explicit replacement
FastAPICache.init(InMemoryBackend(), prefix="second", force=True)

# Or reset first
FastAPICache.reset()
FastAPICache.init(InMemoryBackend(), prefix="second")
```

**Action required:** `FastAPICache` stores one process-global configuration. A normal ASGI worker
should call `init()` once during startup; do not pass `force=True` as a routine lifespan setting.
Tests that enter the same application's lifespan more than once in one process must close any
backend resources they own and call `FastAPICache.reset()` during shutdown/fixture cleanup before
the next startup. If you deliberately replace a live configuration, close the previous backend
first and then use `force=True`. `reset()` clears configuration only; it neither closes backend
resources nor deletes cached data.

`force=True` replaces the global configuration; it does not release resources owned by the
previous backend (for example a Redis connection pool). It also does not isolate two FastAPI
applications running in the same process: the configuration stays global.

Changing the coder while reusing the same backend and namespace can leave entries in an
incompatible format. For example, `PickleCoder` bytes cannot be decoded by `JsonCoder`, and
the read raises `UnicodeDecodeError`. Flush or rotate the namespace when you change the
coder; the library does not delete data automatically.

## Step by step

1. **Inventory.** Note your `fastapi-cache2` version, backend, return types, `clear` usage,
   `key_builder`, headers and authentication.
2. **Characterization tests.** Before migrating, add tests for HIT/MISS, status codes,
   headers and return types so you can compare.
3. **Clean environment.** Create a virtualenv, uninstall `fastapi-cache2`, install
   `fastapi-cache-stable`, and verify `fastapi_cache.__version__`.
4. **Configure once.** Call `FastAPICache.init(...)` once during startup. Define prefix,
   expire, coder and key builder. Review authenticated endpoints.
5. **Run tests.** Expect changes in error responses and `clear()` in `0.3.0a1`; in `0.3.0a2`,
   authenticated requests bypass the cache, InMemory expiry/isolation changes apply, the ETag
   format changes once, `_spec_type` user payloads are preserved, and non-JSON responses
   bypass the cache. A second `init()` now raises `RuntimeError` unless you pass `force=True`.
   Update asserts with the documented behavior.
6. **Flush only affected data.** The default key formula is unchanged, and the ETag change only
   makes clients revalidate; neither requires a full namespace flush by itself. Clear or rotate
   namespaces that contain old authenticated entries before enabling the default auth bypass.
   Flush entries with old `_spec_type` date/datetime/Decimal markers if the restored type matters,
   and clear data written with an incompatible custom coder.
7. **Observe.** Compare HIT/MISS, latency, errors and memory with your baseline.
8. **Roll back if needed.** See below.

## Rollback

```sh
pip uninstall -y fastapi-cache-stable
pip install "fastapi-cache2==0.2.2"
# clear or rotate only data that is incompatible or must be invalidated
```

Keep the previous version pinned and a backup of your configuration. Rollback does not
restore cache entries written with an incompatible coder or marker format; those entries are
regenerated. The default key formula is unchanged, so changing distributions alone does not
require clearing the namespace. Clear or rotate it for old authenticated responses or any
specific incompatible data identified during migration.

**Security warning:** `fastapi-cache2 0.2.2` does not include this fork's default
`Authorization`/`Cookie` bypass. If rollback will serve user-specific endpoints through the
cache, disable caching on those endpoints or configure an identity-aware `key_builder` before
traffic resumes. Clearing Redis removes existing entries but does not prevent the old version
from writing new shared keys.

## FAQ

**Does the import change?** No: `fastapi_cache`.
**Can I install both packages?** No, not in the same environment.
**What happens to my cached data?** The default key formula is unchanged from `fastapi-cache2`
0.2.2, so normal entries remain addressable. ETags are recalculated from the cached response
and clients revalidate. Clear or rotate namespaces containing old authenticated responses before
deploying the new bypass; flush old special-type entries if you depend on date/datetime/Decimal
conversion, or entries affected by the documented error-response/clear bugs.
**Is `0.3.0b1` production-ready?** No. It is a beta for migration and distribution testing.
Test it against your own application before relying on it.
**What is implemented in `0.3.0b1`?** Everything from `0.3.0a2`: error responses are not
cached, opt-in `TypedJsonCoder` for Pydantic v2, `clear()` key/namespace semantics, the
legacy compatibility matrix, the auth/privacy bypass, the InMemory fixes, `Cache-Control`,
the stable ETag, `_spec_type` preservation, and the non-JSON response bypass. It also adds
the explicit second-`init()` contract.
**What is still missing?** `0.3.0` final is not released. Memcached and DynamoDB remain
experimental with unit-level coverage only, and DynamoDB `clear` is still not implemented.
**Is Pydantic v1 supported?** Migration compatibility only. Pydantic v1 is end-of-life
(1.10.27 is the final release) and receives no new security fixes. Typed restoration requires
Pydantic v2.
**Does stable `0.3.0` support Python 3.8–3.10?** Yes, for the documented legacy functional
matrix and installation range `>=3.8,<3.14`. Those EOL interpreters are outside the
security-support matrix; Python 3.11–3.13 are security-supported.
**Is Redis Cluster supported?** Only with the documented limitations; complete namespace
clearing is not promised.
**Are Memcached and DynamoDB supported?** Experimental until they have parity tests.
DynamoDB `clear` is not implemented and the client cleanup issue remains open.
**Is this an official successor?** No. It is an independent fork, not endorsed by the
original author.
**How do I report a bug?** Open an issue on the fork and pick the bug report form. For a
vulnerability, use [private vulnerability reporting](https://github.com/agustin18/fastapi-cache/security/advisories/new)
instead of a public issue; see [SECURITY.md](SECURITY.md).

## Known limitations in 0.3.x

- No tags, stale-while-revalidate, stampede protection or POST caching.
- A second `FastAPICache.init()` call raises `RuntimeError`; initialize once per worker.
  For a deliberate live replacement, close resources owned by the old backend before using
  `force=True`. Tests that re-enter one application's lifespan in the same process should close
  owned resources and call `FastAPICache.reset()` before the next startup. `reset()` does not
  close resources or delete cached data. This behavior shipped in `0.3.0b1`; see
  [Second `init()` call](#second-init-call).
  The auth/privacy, InMemory, `Cache-Control`, ETag, `_spec_type` and non-JSON fixes are
  implemented in `0.3.0a2`.
- Redis standalone is verified with Redis 7 and redis-py 4.6.0; redis-py 5/6 are not
  supported by the current dependency constraint and are untested.
- No full backend parity.
- No perfect OpenAPI/`response_model` behavior.
- No memory cap in `InMemoryBackend`.
- Typed restoration is opt-in via `TypedJsonCoder` and requires Pydantic v2. Pydantic v1
  and unsupported annotations keep the legacy decoded behavior.
- Stable `0.3.0` installs on Python `>=3.8,<3.14`; Python 3.8–3.10 are legacy functional
  compatibility only and are excluded from stable security support. Python 3.11–3.13 are the
  security-supported matrix. Python 3.14 awaits a full CI matrix.
- The 24-month `1.x` support window in `SUPPORT.md` is conditional on the `1.x` release and
  a co-maintainer being in place; no multi-year promise is active today.

## Verification checklist

### Legacy alpha migration checklist (not current stable-release evidence)

The unchecked items below are a retained migration checklist. They are not a record of tests
run against the current PR candidate; use the current release gates below for that status.

- [ ] `pip uninstall fastapi-cache2` and `pip install fastapi-cache-stable==0.3.0a2` in a clean venv.
- [ ] `import fastapi_cache` and `__version__` are correct.
- [ ] Characterization tests pass or are updated with justification.
- [ ] HIT/MISS, status and types verified.
- [ ] `clear(namespace)` and `clear(key)` verified.
- [ ] Rollback tested in staging.

### Previously implemented `0.3.0` fixes

- [x] Two users with different credentials do not share a response (implemented in `0.3.0a2`).
- [x] ETag is stable across worker processes (implemented in `0.3.0a2`).
- [x] Response `Cache-Control`/`max-age` output omits invalid expiry values (implemented in `0.3.0a2`).
- [x] InMemory `expire=None` and instance isolation behave as documented (implemented in `0.3.0a2`).
- [x] Non-JSON responses and metadata-bearing `JSONResponse` are bypassed; responses with
  `Set-Cookie`, `Cache-Control: no-store/private`, or a background task are never cached
  (implemented in `0.3.0a2`).
- [x] `_spec_type` user payloads are preserved (implemented in `0.3.0a2`).
- [x] A second `init()` is explicit (merged on `stable`; ships in `0.3.0b1`).

### Remaining `0.3.0` release gates

These checks are not implied by the historical items above. Release policy and security gates
are tracked in [`SECURITY_DEPENDENCY_INVENTORY.md`](SECURITY_DEPENDENCY_INVENTORY.md).

- [ ] Parse request `Cache-Control` directives correctly; verify `no-store` prevents cache read
  and write for combined, whitespace, and case-varied directives. (`no-cache` alone must follow
  the documented revalidation behavior.)
- [ ] Run a wheel-based E2E that writes ordinary, authenticated, and special-type entries with
  `fastapi-cache2 0.2.2`, then reads or invalidates them with a wheel built from the candidate.
- [ ] Validate the candidate in one owner-maintained Redis application and one separate
  InMemory application or integration fixture; record sanitized outputs and dependency versions.
- [ ] Reconcile all 93 historical GHSA rows in the separate triage register before stable.
- [ ] Build and verify a uniquely versioned RC artifact; repeat the critical migration checks
  against that exact published artifact before stable.

## See also

- [`COMPATIBILITY.md`](COMPATIBILITY.md) — compatibility contract.
- [`CHANGELOG.md`](CHANGELOG.md) — release notes.
- [`SUPPORT.md`](SUPPORT.md) — support policy.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`FORK_ORIGIN.md`](FORK_ORIGIN.md) — fork origin and attribution.

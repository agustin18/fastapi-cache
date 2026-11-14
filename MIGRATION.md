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

> **Status:** this guide describes `0.3.0a1` and the target `0.3.0` behavior. `0.3.0a1`
> implements the error-response fix, the opt-in `TypedJsonCoder`, the `clear()` fixes and the
> legacy compatibility matrix. The auth/privacy bypass, the InMemory
> `expire=None`/instance-isolation fixes, the `Cache-Control` fix, the stable ETag, the
> `_spec_type` namespacing and the non-JSON response bypass are implemented on `stable`
> (unreleased; target `0.3.0a2`). The second-`init` fix is targeted for a later `0.3.0`
> pre-release. Check the installed version before relying on a behavior listed here.

## Who should migrate

- You use `fastapi-cache2` 0.2.2 on Python 3.8–3.13.
- You use `InMemoryBackend` or `RedisBackend` (standalone Redis).
- Your endpoints are GET and return JSON, Pydantic models, dataclasses or standard types.
- You need a maintained package without changing the `fastapi_cache` import.

Python 3.8/3.9/3.10 and Pydantic v1 are end-of-life upstream. They remain supported for
migration so existing applications can move without code changes; they are not a security
recommendation for new deployments.

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
- You need the auth/privacy fix in a published distribution. It is implemented on `stable`
  but not in `0.3.0a1`; it is targeted for `0.3.0a2`. The published alpha still caches
  authenticated requests by default.
- You need the InMemory `expire=None`/instance-isolation fix in a published distribution. It
  is implemented on `stable` but not in `0.3.0a1`; it is targeted for `0.3.0a2`.
- You need the stable ETag, `_spec_type` or non-JSON response fixes in a published
  distribution. They are implemented on `stable` but not in `0.3.0a1`; they are targeted for
  `0.3.0a2`.
- You need the second-`init` fix; it is targeted for a later `0.3.0` pre-release.
- You use Redis Cluster and need complete namespace clearing.
- You need typed restoration on Pydantic v1; the legacy decoded behavior is preserved instead.
  Pydantic v1 is end-of-life; plan an upgrade to Pydantic v2 for typed restoration and
  security fixes.
- You need tags, stale-while-revalidate, stampede protection or POST caching.
- You need perfect OpenAPI/`response_model` behavior or `fastapi-pagination`.

## Install

`0.3.0a1` is a pre-release. Install the exact version:

```sh
pip uninstall -y fastapi-cache2
pip install "fastapi-cache-stable==0.3.0a1"
# with extras:
pip install "fastapi-cache-stable[redis]==0.3.0a1"
```

Do **not** install both distributions in the same environment: they provide the same
`fastapi_cache` package and the version metadata becomes ambiguous.

Verify:

```sh
python -c "import fastapi_cache; print(fastapi_cache.__version__)"
python -c "from fastapi_cache import FastAPICache; print('ok')"
```

### Alpha installation from TestPyPI

`0.3.0a1` is published to TestPyPI and PyPI. TestPyPI is a separate index and may not have
all dependencies. To verify the exact artifact uploaded to TestPyPI, download it from that
index and install the local wheel:

```sh
python -m pip download --no-deps --only-binary=:all: \
  --index-url https://test.pypi.org/simple/ \
  -d testpypi-dist \
  "fastapi-cache-stable==0.3.0a1"

python -m pip install testpypi-dist/*.whl
python -m pip check
python -c "import fastapi_cache; print(fastapi_cache.__version__)"
```

Dependencies are resolved from PyPI by the normal install of the wheel. TestPyPI is for
validating the distribution, not for production. The same version is also published to PyPI.

## Compatibility matrix

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
| Redis Cluster | Unsupported | `clear` limitations documented; no complete namespace clearing |
| InMemory | Verified for basic operations, clear semantics, `expire=None` and instance isolation | Unit tests; each instance owns its store and lock; no size cap yet |
| Memcached | Experimental | No full `clear`/TTL parity |
| DynamoDB | Experimental | `clear` is not implemented; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

> The Redis integration job installs the resolver-selected `redis` version from the project
> constraint (`^4.2.0rc1`), currently 4.6.0, and runs against a Redis 7 service. Other client
> or server versions are not verified in `0.3.0a1`.

## Behavior changes in 0.3.0

These are intentional bug fixes targeted for `0.3.0`. `0.3.0a1` implements the error-response,
typed-decode and clear-semantics fixes; the auth/privacy bypass is implemented on `stable`
(unreleased; target `0.3.0a2`); the remaining changes are targeted for later pre-releases.
Each one will have a regression test and is listed here so you can decide whether it affects
you.

| Change | Before (0.2.2) | After (0.3.0) | Status |
|---|---|---|---|
| Error responses | A cached 404 could be returned as 200 | Responses with status >= 400 are not cached | Implemented in 0.3.0a1 |
| Typed JSON decode | Cache hits returned plain dicts/lists | Opt-in `TypedJsonCoder` on Pydantic v2; default `JsonCoder`, Pydantic v1 and unsupported annotations keep the legacy decoded behavior; validation errors propagate | Implemented in 0.3.0a1 |
| Authenticated requests | Two users could share a cache key | Requests with `Authorization`/`Cookie`/session bypass the cache by default; opt-in with `cache_authenticated=True` and a safe `key_builder` | Implemented on stable (unreleased; target 0.3.0a2) |
| ETag | `hash()` changes per process; header unquoted | Stable SHA-256 digest, quoted weak ETag, weak `If-None-Match` comparison including lists and `*` | Implemented on stable (unreleased; target 0.3.0a2) |
| `clear(key=...)` | Deleted the whole prefix namespace | Deletes only that key; pass the full key | Implemented in 0.3.0a1 |
| Namespace boundary | `clear("app:user")` also deleted `app:users` | Requires the `:` boundary | Implemented in 0.3.0a1 |
| Redis Cluster namespace clear | Partial/unsafe clearing | Raises `NotImplementedError`; use key-only clear or flush out of band | Implemented in 0.3.0a1 |
| `expire=None` in InMemory | Expired almost immediately | Means no expiration; `get_with_ttl` returns `-1` | Implemented on stable (unreleased; target 0.3.0a2) |
| `Cache-Control` | Could emit `max-age=None` or `max-age=-1` | Only valid values; `max-age` is omitted when no valid expiry exists | Implemented on stable (unreleased; target 0.3.0a2) |
| `_spec_type` | User payloads with that key raised `TypeError` | Internal marker is namespaced as `__fastapi_cache_spec_type__`; user data is preserved | Implemented on stable (unreleased; target 0.3.0a2) |
| Non-JSON responses | Streaming/file/redirect could be cached incorrectly | Bypassed unless the coder's `can_encode` supports them | Implemented on stable (unreleased; target 0.3.0a2) |
| Second `init` | Silent no-op | Reconfiguration is explicit and documented | Targeted |

The error-response, typed-decode and clear-semantics fixes are implemented in `0.3.0a1`.
The auth/privacy bypass, InMemory, `Cache-Control`, ETag, `_spec_type` and non-JSON fixes are
implemented on `stable` (unreleased; target `0.3.0a2`). The second-`init` row is targeted for
a later `0.3.0` pre-release.

### Authenticated requests

`0.3.0a1` caches requests with `Authorization`/`Cookie` using the default key. The fix on
`stable` (unreleased; target `0.3.0a2`) bypasses the cache for requests with a non-empty
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

This fix protects the application cache. It does not configure CDN, reverse-proxy, or browser
caching.

**Action required when upgrading from `0.3.0a1` or earlier:** entries written for
authenticated requests may remain under the old default key. The bypass only affects new
requests. Before deploying, clear or rotate the cache namespace, including all
instances/workers and persistent Redis caches. A public request could otherwise read an old
private entry.

### InMemory expiration and isolation

In `0.3.0a1`, `expire=None` expires almost immediately, and `_store`/`_lock` are shared across
all `InMemoryBackend` instances. On `stable` (unreleased; target `0.3.0a2`):

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
header are still emitted. This is implemented on stable (unreleased; target `0.3.0a2`).

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

### `_spec_type` and user payloads

The internal marker is now `__fastapi_cache_spec_type__` instead of `_spec_type`. User
payloads that contain `_spec_type` are preserved as normal data. The decoder only interprets
the namespaced marker when the object contains exactly the marker and `val`; any other shape
is returned unchanged. Old cached entries written with the `_spec_type` marker are no longer
converted to `datetime`/`date`/`Decimal`; flush the cache namespace if you rely on those
conversions.

### Non-JSON responses

`JsonCoder` only caches `JSONResponse` objects. `StreamingResponse`, `FileResponse`,
`RedirectResponse`, plain `Response`, and template responses are returned directly and are
not cached. Custom coders can override `Coder.can_encode()` to opt in; `PickleCoder` can
round-trip response objects. A plain `Response` with a JSON media type is bypassed unless it
is a `JSONResponse` or a custom coder supports it.

**Action required:** if you were affected by cached error responses or by `clear(key=...)`,
flush the cache namespace after upgrading. If you relied on `clear(key=...)` clearing the whole
prefix, switch to `clear()` or `clear(namespace=...)`. If you relied on `clear("app:user")`
deleting `app:users`, use the exact namespace. Redis Cluster users must use key-only clear or
flush the database out of band. Namespace clear is best-effort and not atomic. `clear()` is an
administrative operation; do not expose it to untrusted input. If the ETag changes, clients may
revalidate once.

## Step by step

1. **Inventory.** Note your `fastapi-cache2` version, backend, return types, `clear` usage,
   `key_builder`, headers and authentication.
2. **Characterization tests.** Before migrating, add tests for HIT/MISS, status codes,
   headers and return types so you can compare.
3. **Clean environment.** Create a virtualenv, uninstall `fastapi-cache2`, install
   `fastapi-cache-stable`, and verify `fastapi_cache.__version__`.
4. **Configure once.** Call `FastAPICache.init(...)` once during startup. Define prefix,
   expire, coder and key builder. Review authenticated endpoints.
5. **Run tests.** Expect changes in error responses and `clear()` in `0.3.0a1`; on `stable`,
   authenticated requests bypass the cache, InMemory expiry/isolation changes apply, the ETag
   format changes once, `_spec_type` user payloads are preserved, and non-JSON responses
   bypass the cache. The second-`init` change remains targeted. Update asserts with the
   documented behavior.
6. **Flush if needed.** If the key format or ETag changed, clear the old namespace. For the
   auth bypass, clearing or rotating the namespace is required, not optional.
7. **Observe.** Compare HIT/MISS, latency, errors and memory with your baseline.
8. **Roll back if needed.** See below.

## Rollback

```sh
pip uninstall -y fastapi-cache-stable
pip install "fastapi-cache2==0.2.2"
# clear the cache namespace if the key format changed
```

Keep the previous version pinned and a backup of your configuration. Rollback does not
restore cache entries written with the new format; they are regenerated.

## FAQ

**Does the import change?** No: `fastapi_cache`.
**Can I install both packages?** No, not in the same environment.
**What happens to my cached data?** If the key format or ETag changed, entries are
regenerated. Flush the namespace if you were affected by an error-response or clear bug.
**Is `0.3.0a1` production-ready?** No. It is an alpha for migration and distribution testing.
**What is implemented in `0.3.0a1`?** Error responses are not cached, opt-in `TypedJsonCoder`
for Pydantic v2, `clear()` key/namespace semantics, and the legacy compatibility matrix.
**What is still missing?** Explicit re-`init()` is targeted for a later `0.3.0` pre-release.
The auth/privacy, InMemory, `Cache-Control`, ETag, `_spec_type` and non-JSON fixes are
implemented on `stable` (unreleased; target `0.3.0a2`).
**Is Pydantic v1 supported?** Migration compatibility only. Pydantic v1 is end-of-life
(1.10.27 is the final release) and receives no new security fixes. Typed restoration requires
Pydantic v2.
**Is Python 3.8/3.9 supported?** Migration compatibility is tested. Python 3.8/3.9/3.10 are
end-of-life and are not recommended for new production deployments.
**Is Redis Cluster supported?** Only with the documented limitations; complete namespace
clearing is not promised.
**Are Memcached and DynamoDB supported?** Experimental until they have parity tests.
DynamoDB `clear` is not implemented and the client cleanup issue remains open.
**Is this an official successor?** No. It is an independent fork, not endorsed by the
original author.
**How do I report a bug?** Use the fork's issues (when enabled) or a private security
advisory for vulnerabilities.

## Known limitations in 0.3.x

- No tags, stale-while-revalidate, stampede protection or POST caching.
- The second-`init` fix is not in `0.3.0a1`; it is targeted for a later `0.3.0` pre-release.
  The auth/privacy, InMemory, `Cache-Control`, ETag, `_spec_type` and non-JSON fixes are
  implemented on `stable` (unreleased; target `0.3.0a2`).
- Redis standalone is verified with Redis 7 and redis-py 4.6.0; redis-py 5/6 are not
  supported by the current dependency constraint and are untested.
- No full backend parity.
- No perfect OpenAPI/`response_model` behavior.
- No memory cap in `InMemoryBackend`.
- Typed restoration is opt-in via `TypedJsonCoder` and requires Pydantic v2. Pydantic v1
  and unsupported annotations keep the legacy decoded behavior.
- Python 3.8/3.9/3.10 migration compatibility is tested, but those versions are end-of-life
  and are not recommended for new production deployments.
- The 24-month `1.x` support window in `SUPPORT.md` is conditional on the `1.x` release and
  a co-maintainer being in place; no multi-year promise is active today.

## Verification checklist

### `0.3.0a1`

- [ ] `pip uninstall fastapi-cache2` and `pip install fastapi-cache-stable==0.3.0a1` in a clean venv.
- [ ] `import fastapi_cache` and `__version__` are correct.
- [ ] Characterization tests pass or are updated with justification.
- [ ] HIT/MISS, status and types verified.
- [ ] `clear(namespace)` and `clear(key)` verified.
- [ ] Rollback tested in staging.

### Before `0.3.0` stable

- [ ] Two users with different credentials do not share a response.
- [x] ETag is stable across worker processes (implemented on `stable`, unreleased).
- [x] `Cache-Control`/`max-age` behavior is correct (implemented on `stable`, unreleased).
- [ ] InMemory `expire=None` and instance isolation behave as documented.
- [x] Non-JSON responses (streaming/file/redirect) are bypassed (implemented on `stable`,
  unreleased).
- [x] `_spec_type` user payloads are preserved (implemented on `stable`, unreleased).
- [ ] A second `init()` is explicit.

## See also

- [`COMPATIBILITY.md`](COMPATIBILITY.md) — compatibility contract.
- [`CHANGELOG.md`](CHANGELOG.md) — release notes.
- [`SUPPORT.md`](SUPPORT.md) — support policy.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`FORK_ORIGIN.md`](FORK_ORIGIN.md) — fork origin and attribution.

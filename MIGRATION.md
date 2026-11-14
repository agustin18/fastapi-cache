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
> legacy compatibility matrix. Auth/privacy, ETag, InMemory expiry/isolation, non-JSON bypass,
> `_spec_type` and second-`init` fixes are targeted for later `0.3.0` pre-releases. Check the
> installed version before relying on a behavior listed here.

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
- You need the auth/privacy, ETag, InMemory expiry/isolation, non-JSON bypass, `_spec_type`
  or second-`init` fixes; they are targeted for later `0.3.0` pre-releases.
- You use Redis Cluster and need complete namespace clearing.
- You need typed restoration on Pydantic v1; the legacy decoded behavior is preserved instead.
  Pydantic v1 is end-of-life; plan an upgrade to Pydantic v2 for typed restoration and
  security fixes.
- You need tags, stale-while-revalidate, stampede protection or POST caching.
- You need perfect OpenAPI/`response_model` behavior or `fastapi-pagination`.

## Install

```sh
pip uninstall -y fastapi-cache2
pip install fastapi-cache-stable
# with extras:
pip install "fastapi-cache-stable[redis]"
```

Do **not** install both distributions in the same environment: they provide the same
`fastapi_cache` package and the version metadata becomes ambiguous.

Verify:

```sh
python -c "import fastapi_cache; print(fastapi_cache.__version__)"
python -c "from fastapi_cache import FastAPICache; print('ok')"
```

### Alpha installation from TestPyPI

`0.3.0a1` is published to TestPyPI first. TestPyPI is a separate index and may not have all
dependencies; use the extra index for PyPI:

```sh
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  "fastapi-cache-stable==0.3.0a1"
```

TestPyPI is for validating the distribution, not for production. The same version can be
published to PyPI later.

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
| InMemory | Verified for basic operations | Unit tests; instance isolation is targeted for 0.3.0; the current implementation shares state between instances; no size cap yet |
| Memcached | Experimental | No full `clear`/TTL parity |
| DynamoDB | Experimental | `clear` is not implemented; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

> The Redis integration job installs the resolver-selected `redis` version from the project
> constraint (`^4.2.0rc1`), currently 4.6.0, and runs against a Redis 7 service. Other client
> or server versions are not verified in `0.3.0a1`.

## Behavior changes in 0.3.0

These are intentional bug fixes targeted for `0.3.0`. `0.3.0a1` implements the error-response,
typed-decode and clear-semantics fixes; the remaining changes are targeted for later
pre-releases. Each one will have a regression test and is listed here so you can decide
whether it affects you.

| Change | Before (0.2.2) | After (0.3.0) | Status |
|---|---|---|---|
| Error responses | A cached 404 could be returned as 200 | Responses with status >= 400 are not cached | Implemented in 0.3.0a1 |
| Typed JSON decode | Cache hits returned plain dicts/lists | Opt-in `TypedJsonCoder` on Pydantic v2; default `JsonCoder`, Pydantic v1 and unsupported annotations keep the legacy decoded behavior; validation errors propagate | Implemented in 0.3.0a1 |
| Authenticated requests | Two users could share a cache key | Requests with `Authorization`/`Cookie`/session bypass the cache by default; opt-in with a safe `key_builder` | Targeted |
| ETag | `hash()` changes per process; header unquoted | Stable digest, quoted weak ETag, correct `If-None-Match` | Targeted |
| `clear(key=...)` | Deleted the whole prefix namespace | Deletes only that key; pass the full key | Implemented in 0.3.0a1 |
| Namespace boundary | `clear("app:user")` also deleted `app:users` | Requires the `:` boundary | Implemented in 0.3.0a1 |
| Redis Cluster namespace clear | Partial/unsafe clearing | Raises `NotImplementedError`; use key-only clear or flush out of band | Implemented in 0.3.0a1 |
| `expire=None` in InMemory | Expired almost immediately | Means no expiration | Targeted |
| `Cache-Control` | Could emit `max-age=None` or `max-age=-1` | Only valid values | Targeted |
| `_spec_type` | User payloads with that key raised `TypeError` | Internal marker is namespaced; user data is preserved | Targeted |
| Non-JSON responses | Streaming/file/redirect could be cached incorrectly | Bypassed unless the coder supports them | Targeted |
| Second `init` | Silent no-op | Reconfiguration is explicit and documented | Targeted |

The error-response, typed-decode and clear-semantics fixes are implemented in `0.3.0a1`.
The remaining rows are targeted for later `0.3.0` pre-releases.

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
5. **Run tests.** Expect changes in error responses and `clear()` in `0.3.0a1`; ETag and
   auth changes are targeted for later pre-releases. Update asserts with the documented
   behavior.
6. **Flush if needed.** If the key format or ETag changed, clear the old namespace.
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
**What is still missing?** Auth/privacy defaults, stable ETag, InMemory expiry/isolation,
non-JSON bypass, `_spec_type` collision handling and explicit re-`init()` are targeted for
later `0.3.0` pre-releases.
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
- Auth/privacy, ETag, InMemory expiry/isolation, non-JSON bypass, `_spec_type` and
  second-`init` fixes are not in `0.3.0a1`; they are targeted for later `0.3.0` pre-releases.
- Redis standalone is verified with Redis 7 and redis-py 4.6.0; redis-py 5/6 are not
  supported by the current dependency constraint and are untested.
- No full backend parity.
- No perfect OpenAPI/`response_model` behavior.
- No memory cap in `InMemoryBackend`; instances currently share state, and instance
  isolation is targeted for 0.3.0.
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
- [ ] ETag is stable across worker processes.
- [ ] `Cache-Control`/`max-age` behavior is correct.
- [ ] InMemory `expire=None` and instance isolation behave as documented.
- [ ] Non-JSON responses (streaming/file/redirect) are bypassed.
- [ ] `_spec_type` user payloads are preserved.
- [ ] A second `init()` is explicit.

## See also

- [`COMPATIBILITY.md`](COMPATIBILITY.md) — compatibility contract.
- [`CHANGELOG.md`](CHANGELOG.md) — release notes.
- [`SUPPORT.md`](SUPPORT.md) — support policy.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`FORK_ORIGIN.md`](FORK_ORIGIN.md) — fork origin and attribution.

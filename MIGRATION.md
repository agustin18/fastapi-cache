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

> **Status:** this guide describes the target `0.3.0` behavior. The current `0.3.0a0` alpha
> does not include these changes yet; they land in the `0.3.0` pre-releases. Check the
> installed version before relying on a behavior listed here.

## Who should migrate

- You use `fastapi-cache2` 0.2.2 on Python 3.10–3.13.
- You use `InMemoryBackend` or `RedisBackend` (standalone Redis).
- Your endpoints are GET and return JSON, Pydantic v2 models, dataclasses or standard types.
- You need a maintained package without changing the `fastapi_cache` import.

## Who should not migrate yet

- You need full Memcached or DynamoDB parity. They are experimental in `0.3.x`.
- You use Redis Cluster and need complete namespace clearing.
- You are on Pydantic v1 or Python 3.8/3.9.
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

## Compatibility matrix

| Component | Supported in 0.3.x | Notes |
|---|---|---|
| Python | 3.10–3.13 | 3.14 evaluated after tests |
| FastAPI | versions tested in CI | Pinned range in `pyproject.toml` |
| Pydantic | 2.x | v1 is not supported |
| Redis | standalone, redis-py 5/6 | Cluster: documented limitations |
| InMemory | yes | Instance-scoped; no size cap yet |
| Memcached | experimental | No full `clear`/TTL parity |
| DynamoDB | experimental | No `clear`; `close` fixed |
| Import | `fastapi_cache` | Same as the original |

## Behavior changes in 0.3.0

These are intentional bug fixes. Each one has a regression test and is listed here so you
can decide whether it affects you.

| Change | Before (0.2.2) | After (0.3.0) |
|---|---|---|
| Error responses | A cached 404 could be returned as 200 | Responses with status >= 400 are not cached |
| Authenticated requests | Two users could share a cache key | Requests with `Authorization`/`Cookie`/session bypass the cache by default; opt-in with a safe `key_builder` |
| ETag | `hash()` changes per process; header unquoted | Stable digest, quoted weak ETag, correct `If-None-Match` |
| `clear(key=...)` | Deleted the whole prefix namespace | Deletes only that key |
| Namespace boundary | `clear("app:user")` also deleted `app:users` | Requires the `:` boundary |
| `expire=None` in InMemory | Expired almost immediately | Means no expiration |
| `Cache-Control` | Could emit `max-age=None` or `max-age=-1` | Only valid values |
| `_spec_type` | User payloads with that key raised `TypeError` | Internal marker is namespaced; user data is preserved |
| Non-JSON responses | Streaming/file/redirect could be cached incorrectly | Bypassed unless the coder supports them |
| Second `init` | Silent no-op | Reconfiguration is explicit and documented |

**Action required:** if you were affected by cached error responses or by `clear(key=...)`,
flush the cache namespace after upgrading. If the ETag changes, clients may revalidate once.

## Step by step

1. **Inventory.** Note your `fastapi-cache2` version, backend, return types, `clear` usage,
   `key_builder`, headers and authentication.
2. **Characterization tests.** Before migrating, add tests for HIT/MISS, status codes,
   headers and return types so you can compare.
3. **Clean environment.** Create a virtualenv, uninstall `fastapi-cache2`, install
   `fastapi-cache-stable`, and verify `fastapi_cache.__version__`.
4. **Configure once.** Call `FastAPICache.init(...)` once during startup. Define prefix,
   expire, coder and key builder. Review authenticated endpoints.
5. **Run tests.** Expect changes in ETag, error responses, auth and `clear`. Update asserts
   with the documented behavior.
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
**Is Pydantic v1 supported?** No in 0.3.x.
**Is Python 3.8/3.9 supported?** No in 0.3.x.
**Is Redis Cluster supported?** Only with the documented limitations; complete namespace
clearing is not promised.
**Are Memcached and DynamoDB supported?** Experimental until they have parity tests.
**Is this an official successor?** No. It is an independent fork, not endorsed by the
original author.
**How do I report a bug?** Use the fork's issues (when enabled) or a private security
advisory for vulnerabilities.

## Known limitations in 0.3.x

- No tags, stale-while-revalidate, stampede protection or POST caching.
- No full backend parity.
- No perfect OpenAPI/`response_model` behavior.
- No memory cap in `InMemoryBackend`.
- No guarantee of compatibility with every FastAPI/Pydantic version.
- No multi-year support promise until a co-maintainer is in place.

## Verification checklist

- [ ] `pip uninstall fastapi-cache2` and `pip install fastapi-cache-stable` in a clean venv.
- [ ] `import fastapi_cache` and `__version__` are correct.
- [ ] Characterization tests pass or are updated with justification.
- [ ] HIT/MISS, status, headers and types verified.
- [ ] `clear(namespace)` and `clear(key)` verified.
- [ ] Two users with different credentials do not share a response.
- [ ] ETag is stable across worker processes.
- [ ] Redis/InMemory TTLs behave as documented.
- [ ] Rollback tested in staging.

## See also

- [`COMPATIBILITY.md`](COMPATIBILITY.md) — compatibility contract.
- [`CHANGELOG.md`](CHANGELOG.md) — release notes.
- [`SUPPORT.md`](SUPPORT.md) — support policy.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`FORK_ORIGIN.md`](FORK_ORIGIN.md) — fork origin and attribution.

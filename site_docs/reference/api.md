# Public API reference · published 0.8.0

This page documents public entry points present in **the published
fastapi-cache-stable 0.8.0 wheel and sdist**. It does not advertise
experimental internal APIs, future backend parity, or unreleased
source-only behavior. The exact TTL boundary and decode-before-304 fixes
from [#123](https://github.com/agustin18/fastapi-cache/pull/123) and
[#124](https://github.com/agustin18/fastapi-cache/pull/124) are included
in this tagged release. For exact signatures inspect the
[source at annotated tag v0.8.0](https://github.com/agustin18/fastapi-cache/tree/v0.8.0/fastapi_cache)
and [artifact provenance](releases.md).

## FastAPICache lifecycle

```python
from fastapi_cache import FastAPICache
```

| Public API | Meaning | Compatibility boundary |
|---|---|---|
| `FastAPICache.init(backend, prefix="", expire=None, coder=JsonCoder, key_builder=default_key_builder, cache_status_header="X-FastAPI-Cache", enable=True, cache_authenticated=False, *, force=False)` | Configure process-global cache instance | A second init raises unless `force=True`; multiple apps/lifespans are **not** automatically isolated |
| `FastAPICache.reset()` | Clear process-global configuration | Does **not** remove entries from Redis or other backends; does not automatically close borrowed clients |
| `await FastAPICache.clear(namespace=None, key=None)` | Remove matching backend entries | A namespace is scoped below the configured prefix; not a global Redis flush |
| `FastAPICache.get_backend()` | Retrieve initialized backend | Requires earlier init |

## Cache decorator

```python
from fastapi_cache.decorator import cache

@app.get("/public/items")
@cache(expire=60, namespace="items")
async def items():
    return {"ok": True}
```

| Argument | Published 0.8.0 meaning |
|---|---|
| `expire: Optional[int]` | Seconds of TTL; None uses configured default, potentially unlimited |
| `namespace: str` | Namespace under the configured **process-global prefix**, not implicit app/tenant isolation |
| `coder` | JsonCoder default; TypedJsonCoder opt-in for Pydantic v2 |
| `key_builder` | Explicit function accounting for validated identity, permission and all response-defining dimensions |
| `cache_authenticated: Optional[bool]` | Opt-in caching of authenticated requests only with a complete identity-aware key |
| `infer_response_model: bool` | Opt-in FastAPI response-model inference (disabled by default for legacy compatibility) |
| `vary_headers: Optional[Sequence[str]]` | Explicit public request-header variants; not a substitute for tenant isolation |
| `injected_dependency_namespace: str` | Namespace for injected request/response dependencies |
| `scope: str` | `legacy` default; `app` requires a bound `CacheHandle` (0.8.0) |
| `handle: Optional[CacheHandle]` | Explicit handle; implies app scope (0.8.0) |

FastAPI route decorators must be **above** `@cache`. An HTTP `Vary`
header by itself does not partition a cached object by identity.

## App scope and failure policies — published 0.8.0

```python
from fastapi_cache import CacheConfig, CacheFailurePolicy, CacheHandle
from fastapi_cache.backends.inmemory import InMemoryBackend

backend = InMemoryBackend(max_entries=1_000)
config = CacheConfig(
    backend,
    scope_id="billing",
    prefix="billing",
    failure_policy=CacheFailurePolicy(strict_read=True),
)
handle = CacheHandle(config)
await handle.start(app)  # in the app lifespan

@app.get("/billing/items")
@cache(scope="app", namespace="items")
async def billing_items():
    return {"ok": True}
```

`CacheConfig(backend, *, scope_id, prefix="", expire=None, coder=JsonCoder,
key_builder=default_key_builder, cache_status_header="X-FastAPI-Cache",
enable=True, cache_authenticated=False, failure_policy=CacheFailurePolicy())`
is immutable and borrows the backend. `scope_id` must be a unique stable
identifier; scoped physical keys use a distinct envelope. One handle belongs to
one Starlette app and event loop; call `await handle.aclose()` on shutdown.
`await handle.clear(namespace=None, key=None)` is the scoped clear operation.

App scope is supported for InMemory and standalone Redis only. It does not
detect hidden tenant, identity or locale context; keep an explicit key builder
and `vary_headers`. A second `start` or missing/conflicting binding raises
`CacheScopeError`.

`CacheFailurePolicy(strict_read=False, conservative_write=False,
recover_json=False)` provides independent opt-ins; all default to the legacy
behavior. `strict_read` classifies only Redis transport connection/timeout
errors as `CacheBackendReadError`; authentication, configuration and programmer
errors are not swallowed. `conservative_write` skips the cache write when
encoding fails. `recover_json` recovers legacy JSON values. This is not a retry,
repair or distributed-consistency API; see #112 for residual limits.

## InMemoryBackend — published 0.8.0

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

backend = InMemoryBackend(max_entries=1_000)
FastAPICache.init(backend, prefix="demo")
```

`InMemoryBackend(*, max_entries: Optional[int] = None)` is **shipped in
0.8.0**, but not present in published 0.5.0. `None` retains the
unbounded, process-local default. A positive integer caps **entry count
per backend instance**, never bytes, workers or total process RSS.
`bool`, zero, negative and non-integer capacities fail validation.
The cap is immutable after construction. At capacity, one expired key
is reclaimed if possible, else the least-recently-used key is evicted.
There is no background sweeper; explicit namespace clearing may still
scan all local keys under the async lock.

**TTL note:** the published 0.8.0 InMemory implementation uses
integer wall-clock seconds and an inclusive `ttl_ts <= now` expiry test;
zero and negative TTLs are expired consistently, and a backward wall-clock
jump is not a monotonicity guarantee. See the
[InMemory guide](../guides/inmemory.md).

## Redis standalone

```python
from redis import asyncio as redis
from fastapi_cache.backends.redis import RedisBackend

client = redis.from_url("redis://localhost:6379/0", decode_responses=False)
FastAPICache.init(RedisBackend(client), prefix="demo")
```

Manage your Redis client's lifecycle in the application's lifespan.
Redis Cluster namespace clearing is unsupported; Redis HA/TLS/Sentinel
are not certified by the standalone service matrix.

## Coders and trust

- `JsonCoder` is the default; historical ordinary decoded behavior remains.
- `TypedJsonCoder` uses opt-in typed Pydantic v2 restoration/validation.
- `PickleCoder` deserializes arbitrary pickle bytes. **Never use it for
  attacker-controlled or untrusted cache contents.** Changing the order
  of conditional HTTP decoding requires its own security review.

Malformed cached HIT bytes are decoded before a conditional
`304` in published 0.8.0. Invalid JSON/UTF-8/typed data fails closed and does
not automatically invalidate or retry. The broader corruption/retry policy
remains open under [#112](https://github.com/agustin18/fastapi-cache/issues/112).

**Related:** [compatibility](compatibility.md),
[privacy](../guides/privacy.md),
[migration](../migration.md),
[release history](releases.md).

!!! note "Generated API reference"
    Documentation generation must use the **tagged published release**,
    not post-release `stable` source falsely labeled as the published release.

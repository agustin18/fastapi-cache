# Public API reference · published 0.5.0

This is a **curated reference** to stable, user-facing entry points; it does not advertise internal helpers, experimental backends or unreleased features. Consult the [source at tag v0.5.0](https://github.com/agustin18/fastapi-cache/tree/v0.5.0/fastapi_cache) for exact type signatures.

## `FastAPICache`

```python
from fastapi_cache import FastAPICache
```

| Entry point | Purpose | Notes |
|---|---|---|
| `FastAPICache.init(backend, prefix="", expire=None, coder=JsonCoder, key_builder=default_key_builder, cache_status_header="X-FastAPI-Cache", enable=True, cache_authenticated=False, *, force=False)` | Configure a cache backend once per application process | A second call raises unless deliberate `force=True`. Does not manage or close caller-owned Redis clients |
| `FastAPICache.reset()` | Reset process-global configuration | Does **not** remove stored backend/Redis entries |
| `await FastAPICache.clear(namespace=None, key=None)` | Selectively remove keys or a namespace | Namespace is scoped under the initialized prefix; **not** a global flush |
| `FastAPICache.get_backend()` | Retrieve initialized backend | Raises before initialization |

## `@cache` decorator

```python
from fastapi_cache.decorator import cache

@app.get("/public/items")
@cache(expire=60, namespace="items")
async def items():
    return {"ok": True}
```

| Argument | Published 0.5.0 behavior |
|---|---|
| `expire: Optional[int]` | TTL in seconds; `None` uses the configured default, which may be no expiration |
| `namespace: str` | Application-scoped key namespace |
| `coder` | `JsonCoder` by default; `TypedJsonCoder` for opt-in typed Pydantic v2 decoding |
| `key_builder` | Custom function for validated identity and all response-defining dimensions |
| `cache_authenticated: Optional[bool]` | Only opt in with a **complete identity/permission-aware key** |
| `infer_response_model: bool` | Opt into FastAPI return-annotation response-model inference; disabled by default |
| `vary_headers: Optional[Sequence[str]]` | Explicit allowlist of request headers affecting **public** response variants; no automatic tenant/identity detection |
| `injected_dependency_namespace: str` | Names for injected request/response dependencies |

HTTP `Vary` alone does not partition the library's internal cache. The decorator order is significant: FastAPI route decorators must go **above** `@cache`.

## Backends

=== "InMemory (0.5.0)"

    ```python
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend(), prefix="demo")
    ```

    Per-instance, process-local, **unbounded in published 0.5.0**. [PR #85](https://github.com/agustin18/fastapi-cache/pull/85) merged a capacity argument into **unreleased `stable` source**, not into the 0.5.0 package.

=== "Redis standalone"

    ```python
    from redis import asyncio as redis
    from fastapi_cache.backends.redis import RedisBackend

    client = redis.from_url("redis://localhost:6379/0", decode_responses=False)
    FastAPICache.init(RedisBackend(client), prefix="demo")
    ```

    Close your client in lifespan teardown. Redis Cluster namespace-wide `clear()` is unsupported.

## Next-release source API (not published)

!!! warning "0.5.0 does not accept this argument"
    The following constructor is implemented in `stable` after [PR #85](https://github.com/agustin18/fastapi-cache/pull/85), but is **not part of a published 0.6.0 distribution**. Keep existing `fastapi-cache-stable==0.5.0` installs on their documented unbounded constructor.

```python
InMemoryBackend(*, max_entries: Optional[int] = None)
```

- A **positive integer** caps entry **count per backend instance**. `None` preserves the original unbounded mode; `bool`, zero, negative and non-integer inputs raise `ValueError`.
- `max_entries` is a **read-only property** after construction. Assignments raise `AttributeError`, and dynamic resizing is not supported.
- When full, new keys reclaim one expired entry if available, else evict the least-recently-used entry. The expiry heap does not start a background task.
- This is **not** a byte-memory cap or an aggregate multiworker limit. Explicit namespace clear can still scan the entire local store under the async lock.
- For a source-only example and release requirements see the [InMemory guide](../guides/inmemory.md) and [0.6.0 checklist](https://github.com/agustin18/fastapi-cache/issues/92).

## Coders

- `JsonCoder` is the default and decodes cached JSON into ordinary Python values.
- `TypedJsonCoder` is opt-in for Pydantic v2 and has its own validation contract.
- `PickleCoder` should **never** deserialize untrusted or attacker-modifiable bytes; avoid it in shared stores without integrity guarantees.

**Related:** [Compatibility](compatibility.md) · [Security](../guides/privacy.md) · [Migration](../migration.md) · [Full source](https://github.com/agustin18/fastapi-cache/tree/v0.5.0/fastapi_cache).

!!! note "Automatic reference generation"
    We can evaluate Zensical's `mkdocstrings` integration against tagged source later. Do not generate or publish an API reference from unreleased `stable` changes while labeling it 0.5.0.

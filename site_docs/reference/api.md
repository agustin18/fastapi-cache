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

    Per-instance, process-local, **unbounded in published 0.5.0**. The proposed `max_entries` argument in [#54](https://github.com/agustin18/fastapi-cache/issues/54) is **not released**.

=== "Redis standalone"

    ```python
    from redis import asyncio as redis
    from fastapi_cache.backends.redis import RedisBackend

    client = redis.from_url("redis://localhost:6379/0", decode_responses=False)
    FastAPICache.init(RedisBackend(client), prefix="demo")
    ```

    Close your client in lifespan teardown. Redis Cluster namespace-wide `clear()` is unsupported.

## Coders

- `JsonCoder` is the default and decodes cached JSON into ordinary Python values.
- `TypedJsonCoder` is opt-in for Pydantic v2 and has its own validation contract.
- `PickleCoder` should **never** deserialize untrusted or attacker-modifiable bytes; avoid it in shared stores without integrity guarantees.

**Related:** [Compatibility](compatibility.md) · [Security](../guides/privacy.md) · [Migration](../migration.md) · [Full source](https://github.com/agustin18/fastapi-cache/tree/v0.5.0/fastapi_cache).

!!! note "Automatic reference generation"
    We can evaluate Zensical's `mkdocstrings` integration against tagged source later. Do not generate or publish an API reference from unreleased `stable` changes while labeling it 0.5.0.

# InMemoryBackend

The fastest way to try the decorator is an in-process cache. **No Redis server required.**

## When to use it

- Local development, tests and a single-worker service.
- Cache lifetime is tied to the Python process.
- Each `InMemoryBackend()` instance stores its own entries. A second Uvicorn worker does not see the first worker's values.

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

FastAPICache.init(InMemoryBackend(), prefix="my-app")
```

Initialize this once during the application's lifespan and call `FastAPICache.reset()` during teardown. See the [full working app](../getting-started.md).

## TTL and invalidation

```python
await FastAPICache.clear(namespace="public")
```

The namespace is scoped under your configured prefix, not a command to clear every backend key. `expire=None` preserves entries until explicit clear or process exit; finite TTL entries are discarded on access after expiration.

## Capacity limitations in published 0.5.0

!!! warning "Unbounded dictionary"
    Published 0.5.0 has **no `max_entries` constructor argument**. Expired entries are removed lazily, which means a stream of never-revisited unique keys can grow memory. For high-cardinality traffic, use Redis and configure capacity appropriately.

[Issue #54](https://github.com/agustin18/fastapi-cache/issues/54) is the separately reviewed proposal for an opt-in capacity limit. Do not pass `max_entries` to your published 0.5.0 application until a newer release explicitly ships it.

## Privacy

The storage location does not resolve identity: follow the same [tenant and header-variation review](privacy.md) that you would apply to Redis.

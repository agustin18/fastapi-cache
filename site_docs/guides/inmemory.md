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

[PR #85](https://github.com/agustin18/fastapi-cache/pull/85) is **merged into `stable` but not published**. The following capacity API is **not supported by 0.5.0**.

## Next-release source: bounded InMemory (not yet published)

!!! warning "Source-only example, NOT for fastapi-cache-stable==0.5.0"
    No 0.6.0 wheel, sdist or tag has been published. Use this example only when independently evaluating a reviewed source checkout or candidate; normal users must stay with the published 0.5.0 snippet above.

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

backend = InMemoryBackend(max_entries=1_000)
FastAPICache.init(backend, prefix="my-app")
```

- `max_entries` accepts only a **positive integer** (excluding `bool`) or `None` for historical unbounded mode; invalid capacities raise `ValueError`.
- The limit is **fixed at construction**. `backend.max_entries` is read-only; assigning to it raises `AttributeError`. Dynamic resizing is unsupported.
- At capacity, insertion reclaims **one expired entry first** when possible; otherwise it evicts the least-recently-used entry. Successful reads, including `get_with_ttl`, and writes refresh recency. There is no background sweeper.
- The limit counts **entries in one instance and worker**, not payload bytes, all worker processes or total memory usage. A single entry can be large.
- Ordinary bounded writes use an indexed expiry heap. Explicit namespace clearing may scan all local entries under the async lock; thread/cross-event-loop sharing is not guaranteed.

For shared multiworker caching, use [Redis](redis.md) with appropriate server-side memory policies. The entry limit is not a privacy, rate-limiting or tenant-isolation guarantee. See [#92 release acceptance](https://github.com/agustin18/fastapi-cache/issues/92).

## Privacy

The storage location does not resolve identity: follow the same [tenant and header-variation review](privacy.md) that you would apply to Redis.

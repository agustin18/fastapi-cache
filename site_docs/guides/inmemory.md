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

!!! warning "Exact expiry deadline in the published wheel"
    Published 0.6.0 uses integer wall-clock seconds and a strict
    `ttl_ts < now` comparison. A value may be readable at the exact
    deadline with remaining TTL zero (including immediate/negative expiry).
    [Draft #123](https://github.com/agustin18/fastapi-cache/pull/123)
    proposes the inclusive `<=` boundary for a future release. It has
    **not** changed the published 0.6.0 wheel. A backward wall-clock jump
    can extend the apparent remaining TTL of a still-live entry; there
    is no monotonic expiration guarantee from this process-local backend.

## Capacity in published 0.6.0

!!! warning "Unbounded when omitted"
    Published 0.6.0 keeps the historical unbounded default; expired entries are removed lazily. A stream of never-revisited unique keys can grow memory. Set `max_entries` when you need a hard per-process bound, and use Redis for high-cardinality shared traffic.

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

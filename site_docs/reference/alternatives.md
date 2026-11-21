# Compare caching alternatives

Choosing a library is a question of **migration cost, HTTP semantics, operational needs and maintenance**, not which project has the longest feature list.

!!! info "Scope and verification"
    This snapshot uses upstream project documentation checked on **2026-11-21**. Our capability column refers to the **published 0.5.0** distribution, not draft PRs. Feature support and releases change; always verify a dependency before adopting it. No third-party performance rankings are implied.

## At a glance

| Library | Best fit | Meaningful difference |
|---|---|---|
| **fastapi-cache-stable 0.5.0** | Existing `fastapi-cache2==0.2.2` apps prioritizing low-friction migration | Preserves `fastapi_cache` imports and ordinary default-key contract; modern Redis client profiles, opt-in `vary_headers`, conservative privacy safeguards, published migration/rollback evidence |
| [FastAPI-CacheX](https://fastapi-cachex.readthedocs.io/en/stable/) | Teams wanting a broader HTTP caching and app-cache API | Separate `fastapi_cachex` import and API; documented tags, stale serving, event hooks, application caching, local/distributed coalescing and locks |
| [Cashews](https://github.com/Krukov/cashews) | General async function caching strategies | Tags, locking, early/soft expiration, Redis and in-memory strategies; different programming model |
| [aiocache](https://github.com/aio-libs/aiocache) | Async function/value caching with plugins | Custom serializers and instrumentation plugins; not a drop-in FastAPI HTTP response cache |
| [dogpile.cache](https://github.com/sqlalchemy/dogpile.cache) | Regeneration coordination and backend abstraction | Mature locking/invalidation concepts; not primarily a FastAPI decorator |
| [Redis FastAPI SDK](https://github.com/redis/fastapi-redis-sdk) | New Redis-specific FastAPI integrations | Redis-native integration and observability; different API and installation contract |
| [Yolley/fastapi-cache](https://github.com/Yolley/fastapi-cache) | Evaluating another maintained `fastapi_cache` project | **Import name collision** with our fork; review behavior/migration rather than co-installing either distribution |

## What we prioritize for 0.6.0

<div class="grid cards" markdown>

-   :material-shield-check-outline: **Migration correctness**

    ---

    Retain ordinary key goldens, separate historical private cache entries, preserve verified Redis migration and rollback, and test independent consumers.

-   :material-database-lock-outline: **Bounded in-process caching**

    ---

    [#54](https://github.com/agustin18/fastapi-cache/issues/54) is reviewing an opt-in, entry-count-limited LRU/TTL backend, with actual full-capacity 10k/100k workload benchmarks. **Not shipped in 0.5.0.**

-   :material-chart-timeline-variant: **Optional diagnostics**

    ---

    [#50](https://github.com/agustin18/fastapi-cache/issues/50) proposes typed HIT/MISS/BYPASS/STORE/error signals without exporting keys, credentials or payloads by default. Only include if independently audited.

-   :material-file-document-check-outline: **Documentation people can use**

    ---

    Separate fresh installation from `fastapi-cache2` migration; provide backend, troubleshooting and privacy guidance, a tested example and API reference.

</div>

## Deliberately not promised

A library that offers **tags, distributed coalescing, stale-while-revalidate, locks and a general application cache** may be a better choice for a new app than this compatibility-focused fork. We will not add all of those to claim feature parity in 0.6.0. Likewise, `vary_headers` does not automatically isolate hidden tenant/role state.

Other important limits: Redis Cluster namespace-wide clear is unsupported; DynamoDB/Memcached are experimental; the 0.5.0 InMemory backend is unbounded; Python 3.8–3.10 have functional legacy coverage only.

## How to decide

**Already using `fastapi-cache2`?** Start with the [migration guide](../migration.md) and compare the documented behavior changes. **Starting fresh?** Try the [five-minute install](../getting-started.md) and choose a backend. If you need a broader abstraction and are willing to migrate APIs, look at the alternatives above.

**Sources:** [FastAPI-CacheX feature overview](https://fastapi-cachex.readthedocs.io/en/stable/) · [CacheX technical comparison](https://fastapi-cachex.readthedocs.io/en/stable/COMPARISON/) · [Cashews](https://github.com/Krukov/cashews) · [aiocache](https://github.com/aio-libs/aiocache) · [Redis SDK](https://github.com/redis/fastapi-redis-sdk).

**Our release evidence:** [0.5.0 provenance](releases.md) · [0.6.0 tracker #86](https://github.com/agustin18/fastapi-cache/issues/86).

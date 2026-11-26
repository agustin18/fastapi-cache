# Choose your backend

Pick based on where your FastAPI workers run. The backend affects operational behavior; it does **not** decide which user or tenant is entitled to see a cached result.

| | InMemory | Redis standalone |
|---|---|---|
| Setup | No external service | Running Redis server required |
| Shared across processes? | No | Yes |
| Persistent across worker restart? | No | Redis configuration-dependent |
| Production multiworker use | No shared cache | Recommended path |
| Published 0.8.0 entry-count bound | Opt-in immutable per-instance `max_entries` (unbounded by default); not a byte or per-worker-group cap | Configure Redis eviction separately |
| Previously published 0.5.0 | Unbounded InMemory; no `max_entries` | Redis memory policies remain separate |
| Cache expiry | TTL / optional no-expiry | Redis TTL |
| Scoped namespace clearing | Yes | Yes for supported standalone mode |
| Opt-in app scope (0.8.0) | Supported | Supported for standalone Redis |
| Failure policies (0.8.0) | Supported (strict read is Redis-oriented) | Supported; strict read classifies connection/timeout |
| Recommended for | Dev, tests, single worker | Servers with multiple workers |

<div class="grid cards" markdown>
-   :material-laptop: **Simple app**

    ---

    [Use InMemory](guides/inmemory.md) to begin without external dependencies.

-   :material-server-network: **More than one worker**

    ---

    [Use Redis](guides/redis.md) when workers must share cached entries.
</div>

!!! warning "Unsupported is not the same as experimental"
    Redis Cluster **namespace-wide clearing** is unsupported; TLS, Sentinel, failover and managed transport environments are not certified. Memcached/DynamoDB remain **experimental** and have narrower invalidation/TTL guarantees. See [compatibility](reference/compatibility.md).

### Before caching any response

Read [privacy and tenant safety](guides/privacy.md). Neither backend automatically discovers hidden identity, permission scopes or response-varying middleware inputs. App scope is opt-in and supported for InMemory and standalone Redis; custom, Memcached and DynamoDB backends are not app-scope eligible. See the [API scope contract](reference/api.md#app-scope-and-failure-policies-published-080).

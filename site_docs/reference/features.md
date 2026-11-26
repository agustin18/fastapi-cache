# What ships in 0.8.0?

This page describes features in the **published 0.8.0 wheel and sdist**. PRs and roadmap proposals are not installed features.

## Capabilities

| Capability | Status | Notes |
|---|---|---|
| `fastapi_cache` drop-in import | :material-check-circle: Shipped | Import unchanged from `fastapi-cache2` |
| GET/JSON response caching | :material-check-circle: Shipped | Legacy ordinary default keys preserved |
| Per-process InMemory | :material-check-circle: Shipped | Per-instance; unbounded by default, opt-in `max_entries` in 0.8.0 |
| Standalone Redis | :material-check-circle: Shipped | Redis-py 4.x legacy path, conditional modern versions |
| TTL and namespace/key clearing | :material-check-circle: Shipped | No global Redis `FLUSHDB` |
| ETag / conditional 304 | :material-check-circle: Shipped | HTTP response metadata on tested paths |
| Authorization/Cookie bypass | :material-check-circle: Shipped | Default behavior, not generic custom-auth detection |
| `vary_headers` | :material-check-circle: Shipped | Explicit public header variations, no tenant autodetection |
| App-scoped configuration/lifecycle | :material-check-circle: Shipped (opt-in) | `CacheConfig`/`CacheHandle`; exact InMemory or standalone Redis; legacy singleton default |
| Failure policies | :material-check-circle: Shipped (opt-in) | `CacheFailurePolicy` flags default off; no retry/repair; #112 residual |
| C4 isolation evidence | :material-check-circle: Shipped (descriptive) | App/identity/locale, 304, privacy, cross-process; no performance certification (#100) |
| Typed JSON restoration | :material-check-circle: Opt-in | `TypedJsonCoder`, Pydantic v2 profiles |
| InMemory capacity / LRU | :material-check-circle: Shipped | [PR #85](https://github.com/agustin18/fastapi-cache/pull/85): opt-in immutable per-instance entry-count limit; historical default remains unbounded |
| Cache event callbacks | :material-clock-outline: Proposed | [#50](https://github.com/agustin18/fastapi-cache/issues/50) |
| Argument exclusion | :material-clock-outline: Proposed | [#49](https://github.com/agustin18/fastapi-cache/issues/49), privacy design required |
| Single-flight / distributed locking | :material-flask-outline: Research | Cancellation, lease and stampede design needed |
| Tags / pattern invalidation | :material-flask-outline: Research | Cross-backend index races and TTL |
| Redis Cluster namespace clear | :material-close-circle-outline: Unsupported | Do not confuse with standalone prefix clearing |
| DynamoDB / Memcached | :material-alert-outline: Experimental | Different TTL/invalidation contracts |

## Release traceability

0.5.0 remains tagged at commit `40c86d551b760315f3c6e99f383d6868c6294870`; 0.8.0 artifact provenance is recorded in the [release evidence](releases.md). See that page for SHA-256, checks and maintenance boundaries.

!!! info "No implicit feature flags"
    The presence of a feature on `stable` after the release does **not** imply it exists in the immutable published package. Always check [PyPI](https://pypi.org/project/fastapi-cache-stable/) and the installed version.

# Choose a caching approach

Choose a cache based on your application's migration requirements,
operational maturity, key/tenant isolation, resource limits and measured
correctness. Feature counts and unstable CI performance comparisons
cannot prove that one library is faster, safer or better.

!!! info "Published release versus proposed changes"
    **fastapi-cache-stable 0.6.0 is published**. It includes optional
    bounded InMemory and the current documented authentication and HTTP
    response handling. Published 0.5.0 was unbounded. The TTL deadline
    correction [#123](https://github.com/agustin18/fastapi-cache/pull/123)
    and decode-before-304 correction
    [#124](https://github.com/agustin18/fastapi-cache/pull/124)
    remain **Draft PRs**, not features of 0.6.0.

## What the published 0.6.0 package offers

| Requirement | Published 0.6.0 | Important boundary |
|---|---|---|
| Migration from `fastapi-cache2` | Tested import and ordinary cache key compatibility | Review authentication, response types, explicit Vary and rollback |
| HTTP GET response caching | Cache MISS/HIT, TTL, ETag and conditional 304 | Hidden identity and permission context are not automatically partitioned |
| Shared cache across workers | Standalone Redis | Requires a managed Redis service and failure controls |
| Single-process local cache | Per-instance InMemory | No sharing between workers or independent processes |
| Bounded InMemory | **Shipped**, opt-in `max_entries`, read-only after construction | An entry-count limit is not a payload-byte, total memory or multiworker cap |
| Header variants | Opt-in `vary_headers` | Does not infer tenant or user identity |
| Authenticated requests | Conservative Authorization/Cookie bypass by default | Unrecognized auth context remains an application-owned risk |
| Optional typed JSON | `TypedJsonCoder` | Pydantic v2 typed validation; default JSON remains legacy-decoded |
| Cache event callbacks | **Not shipped** | [#50](https://github.com/agustin18/fastapi-cache/issues/50) design gated |
| Local single-flight | **Not shipped** | [#96](https://github.com/agustin18/fastapi-cache/issues/96) requires correctness/cancellation proof |
| Tags, stale serving, distributed locks | **Not shipped** | More complex invalidation, retention and lease semantics |
| Redis Cluster namespace clear | **Unsupported** | Individual key clearing is not parity with namespace clear |
| Python 3.14 | **Unsupported** | CPython 3.8–3.10 functional legacy only; 3.11–3.13 security-supported server targets |

## Release quality and limitations

Published 0.6.0 has archived wheel/sdist hashes, migration and
security evidence in [release provenance](releases.md). The
historical published-wheel 0.5.0/0.6.0 AB/BA benchmark
[#122](https://github.com/agustin18/fastapi-cache/pull/122)
is merged, but Redis timings changed sign between CI sessions:
**do not claim an observed speedup or regression**.
Further independent hardware measurements and real HTTP socket
tests are tracked under [#100](https://github.com/agustin18/fastapi-cache/issues/100).

For a new application start with the [installation guide](../getting-started.md).
For an existing application, use [migration](../migration.md),
[privacy](../guides/privacy.md) and the [API reference](api.md).
Multiple apps in one process are **not** automatically isolated;
[#99](https://github.com/agustin18/fastapi-cache/issues/99) and
[#103](https://github.com/agustin18/fastapi-cache/issues/103) are
still design issues. Optional single-flight/events/basic Redis resilience
for 0.7.0 are not committed or available.

See the [current roadmap](../roadmap.md) and
[compatibility matrix](compatibility.md) before choosing a
backend or adapting any new proposal.

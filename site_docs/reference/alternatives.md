# Choose a caching approach

Choose a cache based on your application's migration requirements,
operational maturity, key/tenant isolation, resource limits and measured
correctness. Feature counts and unstable CI performance comparisons
cannot prove that one library is faster, safer or better.

!!! info "Published release versus proposed changes"
    **fastapi-cache-stable 0.8.0 is published**. It includes optional
    bounded InMemory and the current documented authentication and HTTP
    response handling. Published 0.5.0 was unbounded. The TTL deadline
    correction [#123](https://github.com/agustin18/fastapi-cache/pull/123)
    and decode-before-304 correction
    [#124](https://github.com/agustin18/fastapi-cache/pull/124)
    are included in published 0.8.0.

## What the published 0.8.0 package offers

| Requirement | Published 0.8.0 | Important boundary |
|---|---|---|
| Migration from `fastapi-cache2` | Tested import and ordinary cache key compatibility | Review authentication, response types, explicit Vary and rollback |
| HTTP GET response caching | Cache MISS/HIT, TTL, ETag and conditional 304 | Hidden identity and permission context are not automatically partitioned |
| Shared cache across workers | Standalone Redis | Requires a managed Redis service and failure controls |
| Single-process local cache | Per-instance InMemory | No sharing between workers or independent processes |
| Bounded InMemory | **Shipped**, opt-in `max_entries`, read-only after construction | An entry-count limit is not a payload-byte, total memory or multiworker cap |
| Header variants | Opt-in `vary_headers` | Does not infer tenant or user identity |
| Authenticated requests | Conservative Authorization/Cookie bypass by default | Unrecognized auth context remains an application-owned risk |
| App-scoped configuration/lifecycle | **Shipped**, opt-in `CacheConfig`/`CacheHandle` for InMemory or standalone Redis | Bucket-key isolation is not automatic tenant detection; one handle per app/loop |
| Failure policies | **Shipped**, opt-in `CacheFailurePolicy` flags | Defaults are legacy; no retry/repair or cross-process consistency guarantee (#112) |
| Optional typed JSON | `TypedJsonCoder` | Pydantic v2 typed validation; default JSON remains legacy-decoded |
| Cache event callbacks | **Not shipped** | [#50](https://github.com/agustin18/fastapi-cache/issues/50) design gated |
| Local single-flight | **Not shipped** | [#96](https://github.com/agustin18/fastapi-cache/issues/96) requires correctness/cancellation proof |
| Tags, stale serving, distributed locks | **Not shipped** | More complex invalidation, retention and lease semantics |
| Redis Cluster namespace clear | **Unsupported** | Individual key clearing is not parity with namespace clear |
| Python 3.14 | **Supported** | Standard CPython 3.14 in 0.8.0 metadata; 3.8–3.10 functional legacy; 3.11–3.14 security-supported server targets; free-threaded 3.14t is outside scope |

## Release quality and limitations

Published 0.8.0 has archived wheel/sdist hashes, migration and
security evidence in [release provenance](releases.md). The
historical published-wheel 0.5.0/0.6.0 AB/BA benchmark
[#122](https://github.com/agustin18/fastapi-cache/pull/122)
is merged, but Redis timings changed sign between CI sessions:
**do not claim an observed speedup or regression**.
Merged [#128](https://github.com/agustin18/fastapi-cache/pull/128) (`f81e60b`) adds
**descriptive** real loopback HTTP socket tests; independent controlled
hardware, fault profiles and preregistered numeric budgets are still tracked
under [#100](https://github.com/agustin18/fastapi-cache/issues/100).

For a new application start with the [installation guide](../getting-started.md).
For an existing application, use [migration](../migration.md),
[privacy](../guides/privacy.md) and the [API reference](api.md).
Published 0.8.0 offers opt-in app scope for supported backends, but does not
detect hidden tenant or identity context automatically; [#53](https://github.com/agustin18/fastapi-cache/issues/53)
remains open. Optional single-flight/events/basic Redis resilience beyond
0.8.0 are not committed or available.

See the [current roadmap](../roadmap.md) and
[compatibility matrix](compatibility.md) before choosing a
backend or adapting any new proposal.

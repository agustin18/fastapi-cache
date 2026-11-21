# Choose a caching approach

Caching choices depend on application requirements, migration cost,
operational maturity, HTTP semantics, security and actual test evidence.
A feature count or an unverified speed comparison is **not** a reason
to claim a library is better. The capability matrix here is our own
project's published contract, not a comparison or endorsement of
other projects.

!!! info "Published vs candidate"
    **0.5.0** is the latest publicly available `fastapi-cache-stable`
    distribution. Optional bounded InMemory exists in merged source
    and in the proposed **0.6.0 candidate** only; it is not available
    in the published 0.5.0 wheel.

## At a glance

| Application requirement | Available in published 0.5.0 | Proposed 0.6.0 | Limits to check |
|---|---|---|---|
| Low-friction migration from an existing installation | Yes, for verified ordinary keys/API | Preserve | Test auth, special encodings and private namespaces before live traffic |
| HTTP GET response caching with TTL/ETag/304 | Yes | Preserve | Response types, conditional headers and custom coders require testing |
| Real standalone Redis shared across workers | Yes | Preserve | Configure client/server memory, access and failure handling |
| Simple process-local InMemory | Yes, unbounded | Preserve | No shared state across workers |
| Bounded process-local InMemory | No | Yes, opt-in `max_entries`, merged code | Counts entries, not payload bytes; readonly after construction |
| Header-based public variants | Yes, opt-in `vary_headers` | Preserve | Only declared headers; no automatic tenant/role discovery |
| Authenticated requests and private data | Default Authorization/Cookie bypass | Preserve | Other auth schemes need a reviewed identity-aware key or bypass |
| Observability callbacks | Not shipped | Out of scope | No automatic metrics/event export |
| Tag-based invalidation / stale serving / single-flight | Not shipped | Out of scope | Requires independent correctness and concurrency design |
| Redis Cluster-wide namespace invalidation | Unsupported | Unsupported | Never confuse with individual key clearing |
| Python 3.14 and later | Unsupported | Unsupported pending qualification | Legacy 3.8–3.10 functional only, not security-maintained |

## What we prioritize for 0.6.0

- **Predictable migration:** preserve ordinary keys and imports, verify
  a real Redis migration and narrowly scoped rollback using exact installed
  distribution files.
- **Safety and transparency:** keep private-response guards, document
  the library/application responsibility boundary and validate real
  consumer behavior with independent evidence.
- **Bounded local caching:** [#85](https://github.com/agustin18/fastapi-cache/pull/85)
  adds an optional read-only constructor cap with indexed expiry tracking
  and least-recently-used eviction. **No published 0.6.0 artifact exists yet.**
- **Release-quality docs:** show version-accurate usage, package metadata
  and working install/migration examples instead of promising unshipped APIs.

## Deliberately not promised

A local entry limit is not a memory-byte or total distributed-memory cap.
A `Vary` header does not magically create application tenant isolation.
There is no general tag invalidation, coalescing, distributed lock, stale
serving or monitoring export contract today. A project needing those
capabilities should evaluate its architectural requirements separately
rather than assuming this library implements them.

## How to decide

**Maintaining an existing app?** Follow the
[migration guide](../migration.md) and run its explicit privacy, key,
Redis and rollback checks.

**Starting a new app?** Start with the
[five-minute install](../getting-started.md), check
[the public API](api.md), [privacy boundaries](../guides/privacy.md)
and [backend comparison](../backends.md). Prefer standalone Redis when
multiple workers need shared data. Use a process-local backend for tests,
development and explicitly accepted single-worker scenarios.

**Need a currently unsupported capability?** Consult the
[roadmap](../roadmap.md) and open a use-case-specific issue with
reproduction, security constraints and expected compatibility rather
than relying on tentative plans.

**Evidence:** [published package provenance](releases.md) and
[0.6.0 release acceptance](https://github.com/agustin18/fastapi-cache/issues/92).

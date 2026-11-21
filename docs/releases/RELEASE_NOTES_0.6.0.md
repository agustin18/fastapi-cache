# fastapi-cache-stable 0.6.0 — draft release notes

> **DRAFT / NOT PUBLISHED — 2026-11-21.** Version metadata in the
> candidate PR is for testing wheel/sdist only. Current public install
> remains `fastapi-cache-stable==0.5.0`. These notes become release
> notes only after the [exact-artifact release gate](RELEASE_CANDIDATE_0.6.0.md)
> is satisfied and publication is explicitly authorized.

## What changes since published 0.5.0

### Optional bounded InMemory

`InMemoryBackend(max_entries=N)` puts a per-instance, entry-count limit
on the in-process backend. When full, a new key first reclaims a single
expired entry when available; otherwise it evicts the least-recently-used
entry. An indexed heap tracks TTL expiry so ordinary bounded writes do
not require sweeping the entire store. Reads refresh recency.

The cap is validated once at construction: positive integer or
`None` (unbounded default), with booleans disallowed.
`backend.max_entries` is **read-only**. Assignments raise
`AttributeError`; dynamic resizing is not supported.

The cap is **not a memory-byte limit** and does not cap or synchronize
multiple Uvicorn workers or thread/event-loop instances. Individual
values can be large; explicit namespace clear can still scan local keys
under a lock; there is no background sweeper or rate limiter.
Omitting `max_entries` preserves the legacy unbounded behavior.
See [PR #85](https://github.com/agustin18/fastapi-cache/pull/85).

### Documentation and validation

A version-aware API guide distinguishes the **published 0.5.0 wheel**
from the merged source that is being prepared as 0.6.0
([PR #93](https://github.com/agustin18/fastapi-cache/pull/93)).
Full candidate readiness requires new installed wheel/sdist
checks, real Redis 7.4 migration and rollback verification,
modern security scans, the exact candidate SHA and two
independent external consumer exercises. Until recorded, those
checks are **not completed release evidence**.

## Compatibility and limitations

- Distribution `fastapi-cache-stable`; import remains `fastapi_cache`.
  Ordinary legacy cache keys and the default `@cache` contract remain
  unchanged; non-default or sensitive legacy keys may need explicit migration.
- Metadata range `>=3.8,<3.14` retains Python 3.8–3.10 as **functional
  legacy compatibility**, not security-supported deployments.
  Production security work targets CPython 3.11–3.13.
- Redis standalone is the supported shared-backend path, with
  interpreter-conditional redis-py ranges. Redis Cluster namespace-wide
  `clear()` is unsupported; Memcached and DynamoDB remain experimental.
- Authorization/Cookie requests bypass caching by default.
  Identity from custom headers, middleware, dependency/context state,
  proxies, or app-defined tenants is not automatically isolated.
  Private responses require a reviewed key strategy or caching bypass.
  Historic private stored keys need deliberate cleanup before migration.
- Cache event hooks, argument omission, distributed locks, stale serving,
  tag invalidation, automatic per-app config and new Python 3.14 support
  are **not part of this candidate**. No superiority, complete feature
  parity or benchmark win is implied.

## Publication decision

**NO-GO pending** [#92](https://github.com/agustin18/fastapi-cache/issues/92),
[#53 privacy signoff](https://github.com/agustin18/fastapi-cache/issues/53),
[#91 two external consumers](https://github.com/agustin18/fastapi-cache/issues/91),
exact final-artifact evidence and explicit manual approval.
Do not treat these draft notes as a PyPI availability statement.

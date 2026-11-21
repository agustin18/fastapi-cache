# Roadmap: what is next?

**0.5.0 is published.** Proposed 0.6.0 features remain unshipped until separately reviewed and released. This page is an approachable overview, not a release authorization.

## Priorities for 0.6.0

| Priority | Issue | What users gain | Boundary |
|---|---|---|---|
| P0 when reproducible | [#53 — hidden identity/tenant inputs](https://github.com/agustin18/fastapi-cache/issues/53) | Correct private-response behavior | No promise of generic autodetection |
| P1 / active PR | [#54 — bounded InMemory](https://github.com/agustin18/fastapi-cache/issues/54) | Optional LRU capacity for a single process | No memory-byte or multiworker guarantee |
| P1 / proposed | [#50 — typed events](https://github.com/agustin18/fastapi-cache/issues/50) | Observe HIT/MISS/BYPASS/error safely | Opt-in; no mandatory telemetry |
| Research | Single-flight | Avoid duplicated same-key computations | Needs cancellation/race tests |
| Design first | [#49 — parameter exclusion](https://github.com/agustin18/fastapi-cache/issues/49) | Stable keys for irrelevant dependencies | No implicit removal of user/tenant/locale |
| Maintenance | [#45 DynamoDB](https://github.com/agustin18/fastapi-cache/issues/45), [#55 FIPS](https://github.com/agustin18/fastapi-cache/issues/55) | Real defect fixes | Isolated from new minor features |
| Research / docs | [#51 Python 3.14](https://github.com/agustin18/fastapi-cache/issues/51), [#48 docs](https://github.com/agustin18/fastapi-cache/issues/48) | New runtime qualification, easier adoption | No untested support claims |

## Why these priorities?

Our strongest promise is **a safe, low-friction migration from `fastapi-cache2`** with familiar keys and imports. We prioritize bounded memory, diagnostics and demonstrated correctness issues ahead of copying a broad caching strategy API.

Cashews, aiocache, dogpile.cache, FastAPI-CacheX, Yolley/fastapi-cache and Redis FastAPI SDK are useful references. The [technical feature map](https://github.com/agustin18/fastapi-cache/blob/stable/ROADMAP.md#competitor-feature-map-docs-snapshot-2026-11-21) is qualitative; it is **not** an independently measured performance ranking.

**Not planned for 0.6.0 without a separate design:** general tag invalidation, distributed locks, rate limiting, circuit breaking, a second public API.

The full [GitHub roadmap](https://github.com/agustin18/fastapi-cache/blob/stable/ROADMAP.md) includes research, historical PRs and release evidence. [Browse issues](https://github.com/agustin18/fastapi-cache/issues).

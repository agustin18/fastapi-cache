# Roadmap: what is next?

**0.5.0 is published.** [#85](https://github.com/agustin18/fastapi-cache/pull/85) is merged in `stable`, but its new API remains **unshipped** until a separately reviewed 0.6.0 artifact exists. This is a roadmap, not release authorization.

## Priorities for 0.6.0

| Priority | Issue | What users gain | Boundary |
|---|---|---|---|
| P0 when reproducible | [#53 — hidden identity/tenant inputs](https://github.com/agustin18/fastapi-cache/issues/53) | Correct private-response behavior | No promise of generic autodetection |
| P1 / code merged, release pending | [#54 — bounded InMemory](https://github.com/agustin18/fastapi-cache/issues/54) | Optional read-only per-instance `max_entries` with LRU/TTL | **Not in 0.5.0**; no byte or multiworker cap |
| P2 / defer by default | [#50 — typed events](https://github.com/agustin18/fastapi-cache/issues/50) | Optional HIT/MISS/BYPASS/error events | **Not implemented/published**; target 0.7.0 outside the scope of 0.6.0 |
| Research | Single-flight | Avoid duplicated same-key computations | Needs cancellation/race tests |
| Design first | [#49 — parameter exclusion](https://github.com/agustin18/fastapi-cache/issues/49) | Stable keys for irrelevant dependencies | No implicit removal of user/tenant/locale |
| Maintenance | [#45 DynamoDB](https://github.com/agustin18/fastapi-cache/issues/45), [#55 FIPS](https://github.com/agustin18/fastapi-cache/issues/55) | Real defect fixes | Isolated from new minor features |
| Research / docs | [#51 Python 3.14](https://github.com/agustin18/fastapi-cache/issues/51), [#48 docs](https://github.com/agustin18/fastapi-cache/issues/48) | New runtime qualification, easier adoption | No untested support claims |

## Why these priorities?

Our strongest promise is **a safe, low-friction migration from `fastapi-cache2`** with familiar keys and imports. We prioritize bounded memory, diagnostics and demonstrated correctness issues ahead of copying a broad caching strategy API.

The [capability gaps and acceptance criteria](https://github.com/agustin18/fastapi-cache/blob/stable/ROADMAP.md#capability-gaps-and-objective-adoption-criteria-2026-11-21) describe future design needs without named vendor comparisons or unverified performance claims.

**Not planned for 0.6.0 without a separate design:** general tag invalidation, distributed locks, rate limiting, circuit breaking, a second public API.

The full [GitHub roadmap](https://github.com/agustin18/fastapi-cache/blob/stable/ROADMAP.md) includes research, historical PRs and release evidence. [Browse issues](https://github.com/agustin18/fastapi-cache/issues).


## Proposed future releases

- **0.7.0:** optional privacy-safe events (#50), local single-flight (#96)
  and installed-distribution benchmarks (#100). Begin support qualification
  for modern Python (#51) and FIPS portability (#55).
- **0.8.0:** bounded, explicitly reviewed tag invalidation (#97) and
  stale-response policies (#98).
- **0.9.0:** independently scoped app/lifespan configuration (#99);
  start design earlier without promising a new public API.

The [quality and adoption tracker](https://github.com/agustin18/fastapi-cache/issues/95)
defines acceptance evidence, not delivery dates. Release approval
requires applicable final artifact/security/migration evidence and
explicit maintainer approval. User feedback is welcome through the
issue tracker, but there is no adoption quota or external-test
requirement for releases or announcements.

# Roadmap: what is next?

> **Updated 2026-11-23 (supersedes the old 0.7 feature table):**
> On GitHub, `stable=0c306a6` is **0.7.0.dev0 source**, not a published
> artifact. #130–#134 merged; #133 actually tested Redis 7.4 server
> stop/restart on an installed wheel with **retries explicitly disabled**.
> For 0.7 we seek a proportionate no-performance-claim #100 deferral
> **only by express reviewer/maintainer acceptance**; first-attempt
> final Phase B with all twenty mandatory jobs and exact-artifact audit are non-deferrable.
> Longer-term target: true app/lifespan isolation, safe local
> single-flight, privacy-minimal events, tags, app cache and resilient HTTP
> behavior, always opt-in and backwards compatible where possible.


**0.6.0 is published.** [fastapi-cache-stable 0.6.0](reference/releases.md)
was released 2026-11-21. `stable` contains subsequent docs and infrastructure; changes
in an unmerged PR are **not installed**. This page describes proposals, not
a shipping date, certification or approval to publish.

## Current 0.7.0 readiness (2026-11-23)

| Track | Verified state | Unfinished acceptance |
|---|---|---|
| [#100](https://github.com/agustin18/fastapi-cache/issues/100) performance | Merged [#120](https://github.com/agustin18/fastapi-cache/pull/120), [#121](https://github.com/agustin18/fastapi-cache/pull/121), [#122](https://github.com/agustin18/fastapi-cache/pull/122): installed 0.6.0 full/smoke and balanced published 0.5.0/0.6.0 comparison | Independent hardware, faults and regression budgets approved before using them; merged #128 (`f81e60b`) adds descriptive real loopback TCP/Uvicorn measurements |
| [#111](https://github.com/agustin18/fastapi-cache/issues/111) backend | Basic InMemory/Redis capability smoke exists; [#123](https://github.com/agustin18/fastapi-cache/pull/123) **merged** (`612e9d6`) corrects exact InMemory TTL deadline in unreleased source | Explicit cross-backend contract, experimental-provider limitations, clock skew and ownership review |
| [#112](https://github.com/agustin18/fastapi-cache/issues/112) failures | [#124](https://github.com/agustin18/fastapi-cache/pull/124) **merged** (`4dc66ad`) corrects malformed cached HIT/304 in unreleased source; broad policy still proposed | Approved corruption/serialization/backend error policy, security tests and opt-in recovery decision |
| [#99](https://github.com/agustin18/fastapi-cache/issues/99) / [#103](https://github.com/agustin18/fastapi-cache/issues/103) architecture | New per-app/non-HTTP APIs **deferred beyond 0.7**; singleton remains | Design issues open; no claim of safe automatic app or tenant isolation |
| [#110](https://github.com/agustin18/fastapi-cache/issues/110) release | Version-neutral Phase B infrastructure merged in [#113](https://github.com/agustin18/fastapi-cache/pull/113) | Exact *final* 0.7.0 wheel/sdist, 20-job first-attempt Phase B, independent hash and security verification, separately approved publishing |

The observed Redis performance difference between historical 0.5.0 and 0.6.0
**changed sign across GitHub-hosted CI sessions**, so no speedup, regression
or threshold is inferred from that evidence. #100 remains open.

[Detailed 0.7.0 execution plan and evidence boundaries](plan-0-7.md).

## Proposed sequencing — user-visible capability before breadth

| Train | What would be different for a consumer | Non-negotiable test before claiming it |
|---|---|---|
| **0.7.0** | Correct exact InMemory TTL boundary, fail-closed decode before HTTP 304, Redis tuple API and a better error-test envelope; **no new public caching feature** | Security/privacy/compatibility risk review, no speed claims, final installed wheel/sdist and 20-job Phase B; no unauthorized tag |
| **0.8.0** | Opt-in app-scoped lifecycle (#99), local bounded same-key single-flight (#96), optional typed privacy-safe events (#50), scoped failure semantics | Two independent concurrent apps, auth/tenant cross-key tests, cancellation creator/waiter tests, unbounded memory/task regressions, disabled-by-default overhead |
| **0.8.x** | FIPS (#55), safe key exclusions (#49), Python 3.14 (#51) only when qualified | Preserve ordinary legacy keys and Python/Redis matrix; do not imply version support without installed evidence |
| **0.9.0** | Tags and invalidation (#97), practical application cache (#103), possibly bounded stale (#98) | TTL/index/clear and invalidate-in-flight race, per-app namespace, stale private-response bypass, stampede/refresh failure and no cross-tenant replay |
| **0.9.x** | Individually qualified standalone/managed/TLS/Sentinel/Cluster profiles (#102) | Real service trials for each topology, lease/fencing review for distributed coordination, no untested namespace-clear guarantee |
| **1.0.0** | Stable core API, migration contract, governance and long-term maintenance commitment | Independent source+artifact audit, supported security and compatibility matrix, runnable examples, explicit LTS policy; no feature parity assertion |
| **1.x** | Additional atomic primitives, distributed leases, telemetry and storage options only if validated | Separate evidence/owner support and clear opt-in boundaries |

Competing products expose more functionality today. **Our distinction is
safe drop-in migration from fastapi-cache2 plus independent negative
security tests**, not a promise to surpass every feature of CacheX,
cashews, aiocache or the Redis SDK. See [roadmap issue #95](https://github.com/agustin18/fastapi-cache/issues/95).

The authoritative published [0.6.0 provenance](reference/releases.md),
[compatibility](reference/compatibility.md) and
[security/tenant limits](guides/privacy.md) are unchanged. Docs on `stable`
must never describe a proposed 0.7.0 behavior as already published.

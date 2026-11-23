# Roadmap: what is next?

**Published:** [fastapi-cache-stable 0.6.0](reference/releases.md), released
2026-11-21. `stable` contains subsequent docs and infrastructure; changes
in an unmerged PR are **not installed**. This page describes proposals, not
a shipping date, certification or approval to publish.

## Current 0.7.0 readiness (2026-11-23)

| Track | Verified state | Unfinished acceptance |
|---|---|---|
| [#100](https://github.com/agustin18/fastapi-cache/issues/100) performance | Merged [#120](https://github.com/agustin18/fastapi-cache/pull/120), [#121](https://github.com/agustin18/fastapi-cache/pull/121), [#122](https://github.com/agustin18/fastapi-cache/pull/122): installed 0.6.0 full/smoke and balanced published 0.5.0/0.6.0 comparison | Independent hardware, real HTTP sockets, faults, regression budgets approved before using them |
| [#111](https://github.com/agustin18/fastapi-cache/issues/111) backend | Basic InMemory/Redis capability smoke exists; [#123](https://github.com/agustin18/fastapi-cache/pull/123) **Draft** corrects exact InMemory TTL deadline | Explicit cross-backend contract, experimental-provider limitations, clock skew and ownership review |
| [#112](https://github.com/agustin18/fastapi-cache/issues/112) failures | [#124](https://github.com/agustin18/fastapi-cache/pull/124) **Draft** addresses malformed cached HIT/304 and proposes a failure-policy RFC | Approved corruption/serialization/backend error policy, security tests and opt-in recovery decision |
| [#99](https://github.com/agustin18/fastapi-cache/issues/99) / [#103](https://github.com/agustin18/fastapi-cache/issues/103) architecture | Design issues open; process-global singleton is current | Accepted app-context and non-HTTP contracts before events, local single-flight or invalidation |
| [#110](https://github.com/agustin18/fastapi-cache/issues/110) release | Version-neutral Phase B infrastructure merged in [#113](https://github.com/agustin18/fastapi-cache/pull/113) | Exact *final* 0.7.0 wheel/sdist, 20-job first-attempt Phase B, independent hash and security verification, separately approved publishing |

The observed Redis performance difference between historical 0.5.0 and 0.6.0
**changed sign across GitHub-hosted CI sessions**, so no speedup, regression
or threshold is inferred from that evidence. #100 remains open.

[Detailed 0.7.0 execution plan and evidence boundaries](plan-0-7.md).

## Candidate scope — not a commitment

| Target | Candidate features | Mandatory design or quality boundary |
|---|---|---|
| 0.7.0 | Accepted #111/#112 correctness slices, [#96 local single-flight](https://github.com/agustin18/fastapi-cache/issues/96), [#50 optional events](https://github.com/agustin18/fastapi-cache/issues/50), basic [#102 standalone Redis resilience](https://github.com/agustin18/fastapi-cache/issues/102) **only if qualified** | Contracts #99/#103/#112 first; default-off options, privacy/cancellation/latency tests; defer unready features to 0.7.x |
| 0.7.x | Python 3.14 (#51) and FIPS (#55) if qualified, experimental-provider corrections | Installed artifacts, version/security evidence, no blanket backend parity |
| 0.8+ | Opt-in per-app config (#99), application cache API (#103) if needed, tags (#97), safe filtering (#49) | App lifecycle isolation, key compatibility and tenant safety |
| 0.9+ | Bounded stale (#98), advanced Redis HA/TLS/Sentinel/Cluster research (#102) | Independent service E2E, no implied Cluster namespace-clear support |
| 1.0 | Public API and support-policy maturity | Explicit ongoing maintenance commitment and independent review |

A *smaller* 0.7.0 with approved correctness changes is preferable to shipping
unsafe concurrency, observability or distributed behavior by a date.

The authoritative published [0.6.0 provenance](reference/releases.md),
[compatibility](reference/compatibility.md) and
[security/tenant limits](guides/privacy.md) are unchanged. Docs on `stable`
must never describe a proposed 0.7.0 behavior as already published.

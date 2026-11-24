# Roadmap: what is next?

**0.7.1 is published.** [fastapi-cache-stable 0.7.1](reference/releases.md)
was released 2026-11-24 as a metadata-only correction over 0.7.0. `stable` contains subsequent docs and infrastructure; changes
in an unmerged PR are **not installed**. This page describes proposals, not
a shipping date, certification or approval to publish.

## 0.7.1 release status (2026-11-24)

| Track | Verified state | Unfinished acceptance |
|---|---|---|
| [#100](https://github.com/agustin18/fastapi-cache/issues/100) performance | Descriptive installed-wheel harness and historical 0.5.0/0.6.0 comparison; no speedup or regression claim | Independent hardware, faults and regression budgets approved before using them; merged #128 (`f81e60b`) adds descriptive real loopback TCP/Uvicorn measurements |
| [#111](https://github.com/agustin18/fastapi-cache/issues/111) backend | Basic InMemory/Redis capability smoke exists; [#123](https://github.com/agustin18/fastapi-cache/pull/123) (`612e9d6`) ships exact InMemory TTL expiry in 0.7.0/0.7.1 | Explicit cross-backend contract, experimental-provider limitations, clock skew and ownership review |
| [#112](https://github.com/agustin18/fastapi-cache/issues/112) failures | [#124](https://github.com/agustin18/fastapi-cache/pull/124) (`4dc66ad`) ships decode-before-304 in 0.7.0/0.7.1; broad policy still proposed | Approved corruption/serialization/backend error policy, security tests and opt-in recovery decision |
| [#99](https://github.com/agustin18/fastapi-cache/issues/99) / [#103](https://github.com/agustin18/fastapi-cache/issues/103) architecture | New per-app/non-HTTP APIs **deferred beyond 0.7**; singleton remains | Design issues open; no claim of safe automatic app or tenant isolation |
| [#110](https://github.com/agustin18/fastapi-cache/issues/110) release | Final 0.7.1 tag, 20-job Phase B, TestPyPI/PyPI parity and hashes are recorded in [release evidence](reference/releases.md) | Preserve the exact-artifact, first-attempt, tag, hash and maintainer-authorization gates for each future release |

The observed Redis performance difference between historical 0.5.0 and 0.6.0
**changed sign across GitHub-hosted CI sessions**, so no speedup, regression
or threshold is inferred from that evidence. #100 remains open.

[Historical 0.7.0 execution plan and evidence boundaries](plan-0-7.md).

## Candidate scope — not a commitment

| Target | Candidate features | Mandatory design or quality boundary |
|---|---|---|
| 0.7.x | Python 3.14 (#51) and FIPS (#55) if qualified, experimental-provider corrections | Installed artifacts, version/security evidence, no blanket backend parity |
| 0.8 | #99 per-app config, #103 app cache scope if justified, #97 tags, #49 safe filtering | Contracts and tenant/key-compatibility review before implementation |
| 0.9+ | Bounded stale (#98), advanced Redis HA/TLS/Sentinel/Cluster research (#102) | Independent service E2E, no implied Cluster namespace-clear support |
| 1.0 | Public API and support-policy maturity | Explicit ongoing maintenance commitment and independent review |

A *smaller*, evidence-backed next release is preferable to shipping unsafe
concurrency, observability or distributed behavior by a date.

The authoritative published [0.7.1 provenance](reference/releases.md),
[compatibility](reference/compatibility.md) and
[security/tenant limits](guides/privacy.md) are unchanged. Docs on `stable`
must describe only shipped behavior; future proposals must not be described
as already published.

# Roadmap: what is next?

**0.7.2 is published.** [fastapi-cache-stable 0.7.2](reference/releases.md)
was released 2026-11-25 with standard CPython 3.14 compatibility and no runtime
or API changes from 0.7.1. `stable` contains subsequent docs and infrastructure; changes
in an unmerged PR are **not installed**. This page describes proposals, not
a shipping date, certification or approval to publish.

## 0.7.2 release status (2026-11-25)

Python 3.14 is included in the published `>=3.8,<3.15` metadata range. The
functional matrix is 3.8–3.14; the server-side security target is 3.11–3.14.
No runtime, import or public API change belongs to this patch. Exact-artifact
Phase B, registry hashes and provenance are recorded in the
[release evidence](reference/releases.md).

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

## Next priority: 0.8 architecture design

The next track is a reviewed design RFC for [#99](https://github.com/agustin18/fastapi-cache/issues/99), [#111](https://github.com/agustin18/fastapi-cache/issues/111) and [#112](https://github.com/agustin18/fastapi-cache/issues/112), with #53 privacy and #100 descriptive performance evidence. No new runtime API is approved or shipped.

[#51](https://github.com/agustin18/fastapi-cache/issues/51) is completed for standard CPython 3.14 in published 0.7.2. Final Phase B passed 25/25 jobs; see the [release evidence](reference/releases.md). Python 3.8–3.10 remain functional legacy targets; 3.11–3.14 are the security target. Free-threaded 3.14t and 3.15 are outside scope; Memcached and DynamoDB remain experimental. Each future release still requires fresh exact-artifact evidence and separate authorization.

## Candidate scope — not a commitment

| Target | Candidate features | Mandatory design or quality boundary |
|---|---|---|
| 0.7.2 (published 2026-11-25) | #51 standard CPython 3.14 compatibility only | Core + real Redis, installed artifacts, existing contract intact; no unsupported extra or security claim |
| 0.8 | #99 app-scoped configuration/lifecycle RFC with #111 backend and #112 error/serialization contracts | Backward-compatible opt-in, privacy, lifecycle, ownership and cancellation design before implementation |
| 0.9 | #97 tags and #49 safe filtering | Tenant-safe keys, race/TTL-index tests and independently reviewed invalidation scope |
| Later, if justified | #98 bounded stale | Separate expiry, failure and cancellation contract; no stale-safety promise |
| 1.0 | Public API and support-policy maturity | Explicit ongoing maintenance commitment and independent review |

[#103](https://github.com/agustin18/fastapi-cache/issues/103) remains a separate
design discussion after 0.8. Advanced Redis HA/TLS/Sentinel/Cluster qualification
([#102](https://github.com/agustin18/fastapi-cache/issues/102)) is not a core
release candidate. Document unsupported configurations; consider a plugin or
separate integration only if justified and independently qualified. Existing
standalone Redis support is unchanged; no Cluster namespace-clear or HA claim.

FIPS (#55) and experimental-provider corrections (#45) remain separate
maintenance tracks, not automatic additions to 0.8. Local single-flight
(#96) and events (#50) follow accepted contracts; outreach (#88) is separate.

A *smaller*, evidence-backed next release is preferable to shipping unsafe
concurrency, observability or distributed behavior by a date.

The authoritative published [0.7.2 provenance](reference/releases.md),
[compatibility](reference/compatibility.md) and
[security/tenant limits](guides/privacy.md) are unchanged. Docs on `stable`
must describe only shipped behavior; future proposals must not be described
as already published.

# 0.7.0 execution plan and evidence gates

**Status: 2026-11-23 — planning, no release date, no tag, no registry GO.**
Latest published artifact remains [fastapi-cache-stable 0.6.0](reference/releases.md).
Source merged after publication is not an installable 0.7.0 release.

## Actual progress (supersedes historical status below)

| Scope | Verified progress | Still required |
|---|---|---|
| [#100](https://github.com/agustin18/fastapi-cache/issues/100) | [#120](https://github.com/agustin18/fastapi-cache/pull/120), [#121](https://github.com/agustin18/fastapi-cache/pull/121), [#122](https://github.com/agustin18/fastapi-cache/pull/122) **merged**; 0.6.0 published-wheel smoke/full and balanced published 0.5/0.6 comparison | Independent controlled hardware, real Redis fault/disconnect cases and **pre-approved** budgets; [#128](https://github.com/agustin18/fastapi-cache/pull/128) provides real loopback HTTP socket measurement in Draft |
| [#111](https://github.com/agustin18/fastapi-cache/issues/111) | Redis tuple smoke; [#123](https://github.com/agustin18/fastapi-cache/pull/123) **merged source** (`612e9d6`), exact InMemory TTL equality; absent from published 0.6.0 | Contract accepted, clock skew limitation, backend ownership and experimental providers |
| [#112](https://github.com/agustin18/fastapi-cache/issues/112) | [#124](https://github.com/agustin18/fastapi-cache/pull/124) **merged source** (`4dc66ad`), decode-before-304; absent from published 0.6.0 | Corruption/serialization/backend error policy, privacy and cancellation |
| [#99](https://github.com/agustin18/fastapi-cache/issues/99), [#103](https://github.com/agustin18/fastapi-cache/issues/103) | New app-scoped and non-HTTP APIs explicitly **deferred out of 0.7**; singleton behavior remains | Design issues stay open for 0.8+; no multi-app/tenant isolation promise |
| [#110](https://github.com/agustin18/fastapi-cache/issues/110) | Version-neutral release pipeline #113 merged | Fresh exact final 0.7.0 SHA + first-attempt 20-job Phase B, security/hashes and separate publication GO |

The historical Redis timing difference between 0.5 and 0.6 changed sign
across GitHub CI sessions. **No performance superiority or regression claim**
follows. Published 0.6.0 is unaffected by the newer merged source changes.

The [0.7.0 candidate checklist](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_CANDIDATE_0.7.0.md),
[performance preregistration protocol](https://github.com/agustin18/fastapi-cache/blob/stable/benchmarks/REGRESSION_BUDGET_PROTOCOL.md)
and [counteraudit packet](https://github.com/agustin18/fastapi-cache/blob/stable/docs/audit/COUNTERAUDIT_0.7.0_HANDOFF.md)
are **planning templates** until accepted and backed by exact evidence.

### Current release decision: NO-GO

The narrow #123/#124 corrections are merged, but complete #111/#112
backend/error contracts remain open; #99/#103 new APIs are deferred for 0.7.
Next qualify independent-host performance and real Redis fault behavior and individually reviewed opt-in candidates #96/#50/basic #102,
deferring unsafe scope to 0.7.x. Last, freeze selected PRs and repeat the
**exact final SHA** 20-job Phase B, wheel/sdist hash, security and
TestPyPI/PyPI workflow with explicit approval. Never publish from the
historical 0.6.0 artifact, a PR synthetic merge SHA, or CI alone.

---

## Historical starting point (2026-11-22; superseded by status above)

| PR | PR status | Related issue | Issue status | What the PR establishes | What it does **not** establish |
|---|---|---|---|---|---|
| [#109](https://github.com/agustin18/fastapi-cache/pull/109) | Merged (`ea38814`) | [#48](https://github.com/agustin18/fastapi-cache/issues/48) | Open | Current-release docs checks and 0.6.0 migration-demo repair | The separate pages launch; immutable version routes or authorized outreach |
| [#113](https://github.com/agustin18/fastapi-cache/pull/113) | Merged (`fb9278c`) | [#110](https://github.com/agustin18/fastapi-cache/issues/110) | Open | Version-neutral release pipeline | A run on the final future 0.7.0 SHA, a tag or PyPI publication |
| [#114](https://github.com/agustin18/fastapi-cache/pull/114) | Merged (`ed50598`) | [#111](https://github.com/agustin18/fastapi-cache/issues/111) | Open | Redis `get_with_ttl()` returns the tuple required by the tested contract | Full conformance of InMemory, Redis, Memcached or DynamoDB |
| [#116](https://github.com/agustin18/fastapi-cache/pull/116) / [#117](https://github.com/agustin18/fastapi-cache/pull/117) | Merged (`fbd90b5`) | [#48](https://github.com/agustin18/fastapi-cache/issues/48) | Open | Stable-only Pages deployment and verified public documentation URL | Immutable version routes, launch outreach or PyPI metadata changes |

The [published 0.6.0 provenance](reference/releases.md) remains immutable.
Do not use source-only tests or post-release `stable` changes to describe its
contents.

## Execution order

| Stage | Work | Acceptance / handoff |
|---|---|---|
| 1 · Documentation | [#48](https://github.com/agustin18/fastapi-cache/issues/48) correct stale references and validate built site | Docs preview CI, release-version regression check, links and anchors; Pages is live from `stable`; immutable version routes remain |
| 2 · Performance baseline | [#100](https://github.com/agustin18/fastapi-cache/issues/100) start from installed published 0.6.0 | Reproducible commands, fixed workload and budgets chosen *before* feature work, raw results, platform metadata and no superiority claims |
| 3 · Backend contract | [#111](https://github.com/agustin18/fastapi-cache/issues/111) + [#112](https://github.com/agustin18/fastapi-cache/issues/112) | Installed wheel/sdist cases for TTL, clear, ownership, failure and corrupt-data policy; experimental backend limits explicit |
| 4 · Architecture RFCs | [#99](https://github.com/agustin18/fastapi-cache/issues/99) + [#103](https://github.com/agustin18/fastapi-cache/issues/103) | Reproduction, design alternatives, default and key-compatibility review; **accepted designs** before new concurrency/events API |
| 5 · Opt-in candidates | [#96](https://github.com/agustin18/fastapi-cache/issues/96), [#50](https://github.com/agustin18/fastapi-cache/issues/50), basic [#102](https://github.com/agustin18/fastapi-cache/issues/102) | Bounded local single-flight, private-data-free events, standalone Redis timeout/disconnect/cancellation tests; separately review or defer |
| 6 · Final 0.7.0 readiness | [#110](https://github.com/agustin18/fastapi-cache/issues/110) exact-artifact release gates | New final-source first-attempt matrix (12 Redis migration + 7 installed security + build), artifact hashes, authenticated security delta and express maintainer release GO |

Stages 2–4 can progress in parallel. **Do not begin stage 5 implementation
before the applicable #99/#103/#112 decisions are accepted.** Stage 1 is
a documentation/public-visibility dependency for optional outreach
([#88](https://github.com/agustin18/fastapi-cache/issues/88)), **not** a
mandatory PyPI release gate. Backend conformance (#111) also informs basic
Redis resilience (#102).

## Performance protocol (infrastructure merged; qualification incomplete)

Start with a **published-distribution-only** baseline from
[issue #100](https://github.com/agustin18/fastapi-cache/issues/100).
Use isolated environments for historical 0.5.0 and current 0.6.0; identify
wheels/sdists by package version and SHA-256. Test representative HTTP
MISS/HIT/304, Authorization bypass, Vary, payload sizes, expiry and
namespace clear. For bounded InMemory, cover 1k/10k/100k keys and LRU/TTL
churn; for standalone Redis 7.4, cover 1/10/100/1000 clients with explicit
resource limits. Report p50/p95/p99, throughput, peak RSS, warm-up/repeats,
environment, errors and raw machine-readable output.

A key-count cap is **not** a memory-byte cap. Do not assert Redis HA, TLS,
Cluster/Sentinel, distributed locks, Python 3.14, or experimental backend
parity from these measurements. Performance thresholds must be agreed before
comparing candidate changes; publish a comparison page only with real results.

## Scope and release decisions

**Candidates, not promises for 0.7.0:** opt-in per-key single-flight (#96),
privacy-minimizing cache events (#50), and basic standalone Redis resilience
(#102). If research or tests remain inconclusive, ship a smaller qualified
0.7.0 or defer features to 0.7.x; do not relax correctness gates to meet a
version number.

**Independent or later tracks:** [#51](https://github.com/agustin18/fastapi-cache/issues/51)
Python 3.14 qualification and [#55](https://github.com/agustin18/fastapi-cache/issues/55)
FIPS portability; [#45](https://github.com/agustin18/fastapi-cache/issues/45)
DynamoDB fixes; [#49](https://github.com/agustin18/fastapi-cache/issues/49)
argument exclusions; [#97](https://github.com/agustin18/fastapi-cache/issues/97)
tags; [#98](https://github.com/agustin18/fastapi-cache/issues/98)
stale policy; broader multi-app changes in #99/#103; advanced Redis HA
qualification in #102.

Keep `fastapi_cache` imports, ordinary legacy keys, default behavior and
the Python 3.8–3.10 **functional legacy** lane. Security-supported target
remains server-side CPython 3.11–3.13 unless a separate evidence-backed
decision changes it. Hidden tenant and identity contexts
([#53](https://github.com/agustin18/fastapi-cache/issues/53)) do not
become automatically safe.

**Completed since the original plan:** #120–#122 provide the published
wheel baseline and historical comparator. Remaining #100 work is
independent-hardware and real-network qualification with agreed budgets.
Close issues based on demonstrated acceptance, not merely on merged code.

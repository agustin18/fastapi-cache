# 0.7.0 execution plan and issue alignment

**Status as of 2026-11-22: planning only.** The latest **published** distribution is
[fastapi-cache-stable 0.6.0](https://pypi.org/project/fastapi-cache-stable/0.6.0/).
Nothing on this page authorizes tagging, TestPyPI/PyPI uploads, enabling GitHub
Pages, outreach or a support-contract change. A merged PR is not proof that an
API is available in the published wheel.

## Verified starting point

| PR / issue | Status | What it establishes | What it does **not** establish |
|---|---|---|---|
| [#109](https://github.com/agustin18/fastapi-cache/pull/109), [#48](https://github.com/agustin18/fastapi-cache/issues/48) | Merged (`ea38814`) | Current-release docs checks and 0.6.0 migration-demo repair | A live Pages site, immutable version routes or authorized outreach |
| [#113](https://github.com/agustin18/fastapi-cache/pull/113), [#110](https://github.com/agustin18/fastapi-cache/issues/110) | Merged (`fb9278c`) | Version-neutral release pipeline | A run on the final future 0.7.0 SHA, a tag or PyPI publication |
| [#114](https://github.com/agustin18/fastapi-cache/pull/114), [#111](https://github.com/agustin18/fastapi-cache/issues/111) | Merged (`ed50598`) | Redis `get_with_ttl()` returns the tuple required by the tested contract | Full conformance of InMemory, Redis, Memcached or DynamoDB |

The [published 0.6.0 provenance](reference/releases.md) remains immutable.
Do not use source-only tests or post-release `stable` changes to describe its
contents.

## Execution order

| Stage | Work | Acceptance / handoff |
|---|---|---|
| 1 · Documentation | [#48](https://github.com/agustin18/fastapi-cache/issues/48) correct stale references and validate built site | Docs preview CI, release-version regression check, links and anchors; **separate** Pages environment approval and live deployment if desired |
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

## Performance protocol for the next implementation PR

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

**Operational next PR after this documentation reconciliation:** an isolated
`#100` benchmark harness and its reproducible 0.6.0 baseline. Close or
retitle issues based on demonstrated acceptance, not merely on merged code.

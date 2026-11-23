# 0.7.0 narrow-scope decision packet — REVIEWABLE / #100 DEFERRAL ACCEPTED / NOT RELEASED

This document prevents issue-count-driven release planning. Source `stable`
at `fb989a06b959b1a6c894cb2c56c0e67722faa543` has version
`0.7.0` release candidate; the **published** package is still `0.6.0`.
Neither this file nor a green CI implies a release GO.

## Proposed release scope (explicit decision still required)

| Included in the 0.7 candidate | Evidence presently available | Limitation |
|---|---|---|
| InMemory exact expiry boundary | #123 merged; deterministic unbounded/bounded tests | Integer wall-clock can move backward; no monotonic guarantee |
| Decode cached HIT before 304 | #124 merged; malformed JSON/UTF-8/typed negative tests | Fail-closed decode, no automatic invalidation; PickleCoder trusts backend bytes |
| Redis get_with_ttl tuple identity | #114 merged; installed conformance tests | Redis TTL sentinels and EX<=0 differ from InMemory |
| Expanded error & ownership tests | #131 merged; read/write/cancel/log tests | Pool recycling alone is not daemon outage; no new failure policy |
| Redis real daemon fault evidence | #133 merged; Docker stop/restart on installed wheel, Python 3.8/3.12/3.13 | Test explicitly uses no Redis client retries; default retry latency and HA unqualified |
| Release & benchmark infrastructure | #130/#132 merged; dev source distinct from published docs, SHA-checked local candidate wheel benchmark | Still requires final wheel, controlled hardware, signed budgets and artifact audit |

Proposed **exclusions** from 0.7.0 (issues remain OPEN):
- #96 single-flight, #50 events, #97 tags and #98 stale-response policy:
  no new runtime API, default/key/serialized-data change or performance claim.
- #99 application-scoped and #103 new standalone caching API:
  no implicit app or tenant isolation; existing process-global singleton stays.
- #102 enhanced Redis resilience **implementation**, TLS, HA, Sentinel/Cluster:
  the #133 real-server-stop/restart *test* is now merged with 36/36
  checks on its final head; it does not qualify default-client retry latency,
  HA, managed failover or broad reconnection guarantees.
- #45 DynamoDB, Memcached parity, #49 key exclusions, #51 Python 3.14,
  #55 FIPS hashing, #48 immutable docs routes: separate future qualification.
- #53 hidden tenant/identity context: NOT fixed or automatically detected;
  application authors must safely account for response-dependent context.

## Minimum acceptance for carried risks (#111/#112)

Keep broad issues #111/#112 OPEN. For the **actual 0.7.0 behavior selected**,
the maintainer/security reviewer must classify every relevant case with
PASS / FAIL / NOT RUN and an owned explicit decision:
- expiry/TTL/clear/ownership for supported InMemory and standalone Redis,
  including exact boundary, empty bytes, EX=0, clock rollback, namespace
  escaping, concurrent cleanup and installed wheel/sdist behavior;
- backend GET/SET error fallback, cancellation propagation and errors
  without key/credential/payload in logs;
- decode/typed errors on HTTP 304, encode errors, Pickle trust boundary,
  cache headers on failed writes and no unbounded retries or private replay;
- experimental Memcached/DynamoDB limitations as unsupported/unqualified,
  without pretending identical sentinel/close/clear semantics;
- negative authentication/tenant/Vary cases and truthful application-owned
  hidden-context caveats.

A **reproduced package-owned P0/P1** in this selected scope blocks release
even when the broad issue is otherwise deferred. A NOT RUN gate must be
accepted as an explicit limited support statement, never counted as PASS.

## 2026-11-23 risk-based revision to the performance gate — MAINTAINER ACCEPTED

For this **correctness-only** 0.7.0, the maintainer expressly accepted
on **2026-11-23** the **no independent controlled-hardware regression
certification** as a release-specific deferral of the *research portion*
of #100, subject to all conditions below:
- no performance superiority, production p95/p99, latency bound, Redis
  default-retry latency, or HA claim is made in notes, README or public docs;
- unchanged production runtime code paths continue passing real Redis,
  installed-wheel/sdist migration, HTTP socket and bounded InMemory scaling;
- independent review finds no material new regression, P0/P1, or unsupported
  public claim; the actual selected change scope is kept fixed;
- no new perf-sensitive public API, lock policy, stale mode, or background
  callback is slipped into this release.

This is **not** evidence of equal or better speed and is **not** an
independent PASS: the maintainer decision is recorded, while the
independent reviewer must still verify the conditions before final freeze.
If a measured regression, latency feature or speed claim enters scope,
the complete independently controlled AB/BA, numerical budgets preapproved
before measurement, raw samples and provenance in #100 become mandatory.
Keep #100 OPEN as a 0.8+ quality/performance track if this deferral passes.
Never loosen first-attempt 20/20 Phase B, fresh security review or
independent exact-artifact counteraudit.

## Hard prerelease gates (cannot be satisfied by this document)

1. **Full #100 budget protocol applies ONLY if needed for a speed claim,
   new performance feature or material suspected regression**. The maintainer
   accepted the no-claim deferral above on 2026-11-23; the independent reviewer
   must still validate it. The original full protocol would require a
   controlled independently managed CPU/RAM/OS environment, identical
   installed-wheel dependency freeze, pairwise AB/BA scenario order, warmup,
   repeat/sample counts, metrics and *numeric* allowed regressions and
   errors in `benchmarks/REGRESSION_BUDGET_PROTOCOL.md` or a signed manifest.
   Existing GitHub shared-runner numbers do not decide the budget.
2. If the full protocol is triggered, run controlled baseline `0.6.0`
   versus final candidate on that host:
   HTTP real sockets (HIT/MISS/304/Vary/auth/TTL) and Redis/InMemory,
   raw CSV/JSON, independent repeat variance and inconclusive policy.
   Require evidence of real standalone Redis fault/reconnect (not pool
   recycle). Do not claim production p99 based on 120 serial samples.
3. Review/merge only selected fixes, prepare a separate **final 0.7.0
   promotion PR** (metadata, changelog, release notes and version-aware
   fixtures). Keep `PUBLISHED_VERSION=0.6.0` until publication really
   occurs; frozen source is a candidate, not a published install instruction.
4. Freeze one full `stable` SHA, run a **fresh manual first-attempt
   20-job Phase B** on that SHA (1 build + 12 real Redis migration/rollback
   + 7 installed security); independently verify wheel+sdist hashes,
   provenance and fresh authenticated Dependabot/lock security delta.
5. Fill all TBD fields in the [independent handoff](../audit/COUNTERAUDIT_0.7.0_HANDOFF.md).
   Obtain independent adversarial review. Any material finding/source
   change invalidates stale SHA/hash evidence and triggers a new review.
6. Only after explicit maintainer GO: create annotated `v0.7.0` tag,
   verify tag object and target, separately approve exact-byte TestPyPI,
   then separately approve PyPI. Validate published distributions, registry
   hashes, GitHub Release and updated documentation marker afterwards.

**Decisions requested from maintainer:** accept narrow scope and exclusions;
approve the risk classification (#111/#112/#53); the #100 no-claim deferral
is **ACCEPTED by the maintainer on 2026-11-23** and still needs independent
reviewer validation; authorize final-release preparation only when those
gates are evidenced. Nothing here grants permission to tag, publish, modify
branch protection or silently close open issues.

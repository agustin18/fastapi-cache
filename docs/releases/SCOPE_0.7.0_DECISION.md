# 0.7.0 narrow-scope decision packet — PROPOSED / NOT ACCEPTED

This document prevents issue-count-driven release planning. Source `stable`
at `1d7815493ebe36c3ad58095e12a1ed1ab9f679bc` has version
`0.7.0.dev0`; the **published** package is still `0.6.0`.
Neither this file nor a green CI implies a release GO.

## Proposed release scope (explicit decision still required)

| Included in the 0.7 candidate | Evidence presently available | Limitation |
|---|---|---|
| InMemory exact expiry boundary | #123 merged; deterministic unbounded/bounded tests | Integer wall-clock can move backward; no monotonic guarantee |
| Decode cached HIT before 304 | #124 merged; malformed JSON/UTF-8/typed negative tests | Fail-closed decode, no automatic invalidation; PickleCoder trusts backend bytes |
| Redis get_with_ttl tuple identity | #114 merged; installed conformance tests | Redis TTL sentinels and EX<=0 differ from InMemory |
| Expanded error & ownership tests | #131 merged; read/write/cancel/log tests | Pool recycling is not daemon outage; no new failure policy |
| Release & benchmark infrastructure | #130/#132 merged; dev source distinct from published docs, SHA-checked local candidate wheel benchmark | Still requires final wheel, controlled hardware, signed budgets and artifact audit |

Proposed **exclusions** from 0.7.0 (issues remain OPEN):
- #96 single-flight, #50 events, #97 tags and #98 stale-response policy:
  no new runtime API, default/key/serialized-data change or performance claim.
- #99 application-scoped and #103 new standalone caching API:
  no implicit app or tenant isolation; existing process-global singleton stays.
- #102 enhanced Redis resilience **implementation**, TLS, HA, Sentinel/Cluster:
  a narrowly scoped real-server-stop/restart *test* may ship after review
  (PR #133), without promising general reconnect or outage guarantees.
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

## Hard prerelease gates (cannot be satisfied by this document)

1. **Budget approval BEFORE performance testing**: #100 must name a
   controlled independently managed CPU/RAM/OS environment, identical
   installed-wheel dependency freeze, pairwise AB/BA scenario order, warmup,
   repeat/sample counts, metrics and *numeric* allowed regressions and
   errors in `benchmarks/REGRESSION_BUDGET_PROTOCOL.md` or a signed manifest.
   Existing GitHub shared-runner numbers do not decide the budget.
2. Run controlled baseline `0.6.0` versus final candidate on that host:
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
approve the risk classification (#111/#112/#53); separately approve numeric
performance budgets *before* measurements; authorize final-release preparation
only when those gates are evidenced. Nothing here grants permission to tag,
publish, modify branch protection or silently close open issues.

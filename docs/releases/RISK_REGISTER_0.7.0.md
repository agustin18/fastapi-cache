# 0.7.0 security, correctness and compatibility risk register — MAINTAINER DECISION RECORDED; INDEPENDENT REVIEW PENDING

**Scope:** source at pre-preparation `fb989a06b959b1a6c894cb2c56c0e67722faa543`
only; will change if release-promotion PRs merge. Published artifact remains
`fastapi-cache-stable==0.6.0`. This record is a **review request**, not
maintainer acceptance or independent approval. Populate evidence with
**exact SHA / run URL / installed-wheel digest** before final GO.

| Gate | Current characterized behavior | Unqualified residual / negative test | Proposed release treatment | Reviewer verdict |
|---|---|---|---|---|
| #111 InMemory expiry | #123 expiry at integer deadline; bounded/unbounded deterministic tests | Wall-clock rollback can increase TTL for a still-live entry | Document as wall-clock, not monotonic; no hidden promise | NOT REVIEWED |
| #111 Redis TTL | #114 returns tuple; #131 missing/empty bytes and EX=0 divergence | Redis has -2 miss vs InMemory 0; EX<=0 rejects | Document per-backend semantics, do not normalize in 0.7 | NOT REVIEWED |
| #111 scoped clear and ownership | Scoped key/namespace tests; #131 caller owns Redis client | Redis Cluster namespace clear unsupported; experimental providers not conformance-qualified | Supported InMemory/standalone Redis only | NOT REVIEWED |
| #102 Redis real daemon fault | #133 installed wheel, Docker stop/restart, Python 3.8/3.12/3.13 | Probe sets Retry(NoBackoff(),0); redis-py default retries may exceed 3s watchdog, no HA/timeout SLO | Characterization, not runtime policy/HA claim | NOT REVIEWED |
| #112 backend read/write | #131 read fail recomputes, write fail response may carry ETag even without storage | No universal retry, eviction, cache-header persistence contract | Preserve existing behavior; document ETag is representation not proof of storage | NOT REVIEWED |
| #112 decode/304 | #124 decodes cached bytes before checking If-None-Match | Corrupt data fails closed; no auto-eviction/recompute; typed/codec matrix incomplete | Fail-closed explicitly; P0/P1 leak remains blocking | NOT REVIEWED |
| #112 cancellation | #131 CancelledError propagates for synthetic read | Concurrent write race, in-flight refresh, real outage cancellation unqualified | No single-flight, locks, callbacks or recovery API in 0.7 | NOT REVIEWED |
| #112 PickleCoder | Explicit legacy PickleCoder uses pickle.loads | Arbitrary code execution if attacker can modify pickle bytes | Never use with untrusted/shared mutable Redis; prefer JsonCoder; no auto-unpickle policy | NOT REVIEWED |
| #53 auth/tenant/Vary | Credential headers bypass; opt-in Vary; explicit Request unsafe default bypass | Middleware/contextvars/custom auth/tenant inputs not automatically part of keys | Application must provide safe key partition or bypass; do not claim generic isolation | NOT REVIEWED |
| #100 performance | #120–#122 published baseline, #128 real socket, #133 process outage | CI runners unstable; no independent hardware/approved numerical budgets; default redis-py retry latency unqualified | **Maintainer accepted** the no-claim fixed-host deferral on 2026-11-23; not speed certification | MAINTAINER ACCEPTED / REVIEWER PENDING |
| #110/#126 release bytes | Version-neutral pipeline and 0.6.0 precedent | No 0.7 final SHA, 20/20 Phase B, frozen hashes, security delta or independent artifact review | Mandatory before tag/registry GO; NO DEFERRAL | BLOCKED |

## Mandatory maintainer/reviewer decisions

- [ ] Accept/reject only this narrow behavior and exact legacy import/key
      compatibility; leave feature issues #96/#50/#99/#103/etc. open.
- [ ] Classify real P0/P1 findings and any exploitable package-owned
      tenant/identity leak. A confirmed P0/P1 is a NO-GO, not a documentation
      deferral. Do not disclose unpatched exploit details in a public issue.
- [x] **ACCEPT** the no-performance-claim deferral for #100, recorded
      by the maintainer on 2026-11-23. The independent reviewer must still
      validate it; if a speed claim or material regression appears, require
      full independently controlled, preregistered numeric AB/BA.
      Green CI alone is not approval.
- [ ] Independently reproduce important negative paths with installed
      artifacts; do not mark NOT RUN as PASS.
- [ ] Approve or reject unchanged metadata support Python 3.8–3.10
      functional legacy / 3.11–3.13 security supported; 3.14 unqualified.
- [ ] Freeze source and candidate artifacts, record reviewer identity,
      decision date, exact source SHA/20-job run, two digest checks,
      authenticated security delta and explicit acceptance/rejection of
      residual risk.

**Never publish based solely on this unsigned risk inventory.**

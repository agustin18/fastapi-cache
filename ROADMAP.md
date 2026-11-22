# Roadmap — fastapi-cache-stable

**Current published release:** [0.6.0](https://pypi.org/project/fastapi-cache-stable/0.6.0/)
on **2026-11-21**. It adds opt-in bounded InMemory and the 0.6.0
authentication/HTTP privacy corrections. See
[0.6.0 release evidence](docs/releases/RELEASE_STATUS_0.6.0.md).
**0.5.0** remains the previous published line. Source version and
merged PRs alone do not imply publication.
**Do not reopen a completed publication gate without new material evidence.**

**0.5.0 release record:** #67/#68 closed; #69 Phase A [#80](https://github.com/agustin18/fastapi-cache/pull/80)
and Part B [#82](https://github.com/agustin18/fastapi-cache/pull/82) complete;
#53 opt-in `vary_headers` merged in [#81](https://github.com/agustin18/fastapi-cache/pull/81),
with residual hidden tenant/context/cardinality risks still tracked. The final
stable SHA passed 13/13 Phase B, 7/7 installed security profiles, a fresh
authenticated Dependabot delta (21 unchanged open) and the exact-artifact
release checks in [#66](https://github.com/agustin18/fastapi-cache/issues/66).

Everything below is a **candidate plan, not a delivery promise**.
The primary product advantage remains conservative migration from
`fastapi-cache2==0.2.2`, preserved `fastapi_cache` imports, predictable
cache keys and safe default HTTP/private-response behavior.


## 0.6.0 — published and verified

The 0.6.0 final source is tagged at `6b6924a61bbcc0ba602da514accb4c563806742f`,
with published wheel/sdist hashes, all twenty final Phase B jobs,
TestPyPI/PyPI parity and maintainer risk acceptance documented in
[release evidence](docs/releases/RELEASE_STATUS_0.6.0.md).
Optional bounded InMemory, authentication and HTTP-cache privacy corrections
are **shipped**, not future proposals. Historical 0.5.0 remains immutable.

[#53](https://github.com/agustin18/fastapi-cache/issues/53) stays open for
application-owned hidden tenant/context/cardinality limitations and future
reproducible package-controlled issues. No independent consumer quota,
third-party security certification or hosted-docs requirement applies.

## Immediate P0/P1 — 0.7.0 qualification status

See the [separate 0.7.0 execution and issue-alignment page](site_docs/plan-0-7.md). It is a plan, not a release promise.

- **P0 release infrastructure:** [#110](https://github.com/agustin18/fastapi-cache/issues/110),
  [merged PR #113](https://github.com/agustin18/fastapi-cache/pull/113) (`fb9278c`).
  The version-neutral infrastructure is merged, without any 0.7.0 tag or upload.
  Preserve exact-artifact, 20-job first-attempt, tag, approved hashes and
  TestPyPI parity gates. A synthetic 0.7.0 dry-run cannot replace new
  release-specific final installed evidence or maintainer authorization.
- **Public documentation:** [#48](https://github.com/agustin18/fastapi-cache/issues/48),
  [merged PR #109](https://github.com/agustin18/fastapi-cache/pull/109) (`ea38814`).
  Current release references and demo checks were updated. The public site is
  live at <https://agustin18.github.io/fastapi-cache/> and deploys only from
  `stable` through merged #116/#117 (`fbd90b5`); the build job is read-only and
  the `github-pages` environment is restricted to `stable`. Versioned
  `/latest/` and immutable `/0.6.0/` routes remain planned. [#88](https://github.com/agustin18/fastapi-cache/issues/88)
  publicity separately requires explicit authorization for this launch.
- **Backend capability contract:** [#111](https://github.com/agustin18/fastapi-cache/issues/111)
  ahead of backend fixes [#45](https://github.com/agustin18/fastapi-cache/issues/45):
  TTL, clear, close, cancellation, timeouts and declared limitations.
  [Merged PR #114](https://github.com/agustin18/fastapi-cache/pull/114)
  (`ed50598`) fixed Redis `get_with_ttl()` tuple conformance; this is only
  a subset of the broader installed-distribution contract in #111.
- **Corrupt data and serialization:** [#112](https://github.com/agustin18/fastapi-cache/issues/112)
  defines fail-open/closed, trust, privacy and error propagation.
- **Benchmarks:** [#100](https://github.com/agustin18/fastapi-cache/issues/100)
  starts with installed, published 0.6.0 and reproducible performance results.
- **Architecture RFCs:** [#99](https://github.com/agustin18/fastapi-cache/issues/99)
  (app/lifespan-scoped configuration) and [#103](https://github.com/agustin18/fastapi-cache/issues/103)
  (non-HTTP cache scope) must be accepted before implementing
  [#96](https://github.com/agustin18/fastapi-cache/issues/96) local single-flight
  or [#50](https://github.com/agustin18/fastapi-cache/issues/50) events.

## Staged capability releases — proposals, not dates

| Release | Focus | Non-negotiable boundary |
|---|---|---|
| **0.7.0** | #100 published baseline, opt-in #96 single-flight and #50 privacy-safe events, #102 **basic** Redis timeout/reconnect/cancellation; conditional #51 Python 3.14 | #110 + RFCs #99/#103 + #112 first; split features to 0.7.x if not ready |
| **0.7.x** | #55 FIPS and evidence-backed nonbreaking experimental backend corrections | Legacy default keys and published support boundaries unchanged |
| **0.8.0** | #99 optional per-app lifecycle, #97 tags, #103 application cache only if justified, #49 parameter exclusions | Tenant isolation, TTL indexes, race tests and explicit opt-in |
| **0.9.0** | #98 bounded stale, #102 advanced TLS/Sentinel/Cluster/HA qualification, distributed coordination research | Separate backend profiles; no blanket HA or stale safety claims |
| **1.0.0** | Public API and maintenance-contract maturity | Support duration decision separate; do not promise 24 months without sustainable maintenance |

Every feature release requires reproducible exact wheel/sdist installation,
supported-runtime/Redis matrix, risk triage, concurrency/error tests,
benchmark budgets and accurate browsable documentation. Do not publish
unimplemented features in the public API guide.

## 0.4.0 — delivered Redis compatibility (2026-11-20)

Shipped:

- [#47](https://github.com/agustin18/fastapi-cache/issues/47): Python-conditional
  redis-py ranges, preserving 4.x and admitting tested 5.x/6.x/7.x/8.x clients
  by interpreter. RedisBackend cache-key and serialization semantics did not change.
- [#62](https://github.com/agustin18/fastapi-cache/pull/62): research matrix over
  Python 3.8–3.13, redis-py 4.6–8.1 and Redis 6.2/7.0/7.4/8.0 with installed-wheel
  and consumer probes.
- [#63](https://github.com/agustin18/fastapi-cache/pull/63): release-shaped wheel/sdist
  matrix, metadata regression and mandatory support lanes.
- [#64](https://github.com/agustin18/fastapi-cache/pull/64): version, changelog,
  release notes and documentation.
- Earlier maintenance delivered in the 0.3.x/0.4.0 path: [#44](https://github.com/agustin18/fastapi-cache/issues/44)
  (uvicorn removed), [#46](https://github.com/agustin18/fastapi-cache/issues/46)
  (read-only Dependabot delta) and the #61 distribution-metadata regression.

`0.3.1` remains the earlier migration line and retains its own release history in
[docs/releases](docs/releases/). Published 0.4.1 resolved #68's generated route replay; published 0.5.0
adds explicit opt-in HTTP `Vary` for known header dimensions.
[#53](https://github.com/agustin18/fastapi-cache/issues/53)
stays open for residual hidden context/tenant identity, proxy trust,
header cardinality and authentication/HTTP-cache safety review. Neither explicit-`Request`
bypass nor `vary_headers` automatically makes an application's
unknown identity dimensions safe.

## 0.4.x — maintenance candidates (no release date promised)

| Priority | Focused issue | Deliverable / acceptance |
|---|---|---|
| **P1** | [#55: MD5/FIPS key portability](https://github.com/agustin18/fastapi-cache/issues/55) | Reproduce restricted-hash failures; retain legacy key digests and **Python 3.8** support. Upstream `usedforsecurity=False` needs version-specific handling |
| **P1** | [#45: DynamoDB correctness](https://github.com/agustin18/fastapi-cache/issues/45) | Reproduce/fix expired-value reads and client cleanup lifecycle if verified; keep DynamoDB experimental |
| **Delivered in 0.4.1** | [#68: factory-route key collision](https://github.com/agustin18/fastapi-cache/issues/68) | Closed: published fix separates generated/wrapped handler keys without globally rewriting default keys; verify published 0.4.1 or later |
| **Published in 0.5.0** | [#53: Vary opt-in and residual](https://github.com/agustin18/fastapi-cache/issues/53) | Explicit hashed `:vary-v1:` keys with returned Response `Vary` on MISS/HIT/304. Issue stays open for hidden identity/tenant/proxy/cardinality limits |
| **P2 — conditional** | [#51: Python 3.14 qualification](https://github.com/agustin18/fastapi-cache/issues/51) | Full functional/security matrix must pass before changing metadata; otherwise stay out of range |

A `0.4.x` release is **not mandatory for docs-only or CI-only merges**;
batch a small, regression-tested fix and publish only when there is
user-facing value. Do not change cache keys or the Python/Redis metadata
ranges without a verified compatibility lane.

## 0.5.0 — published secure migration release

**Release tracker: [#70](https://github.com/agustin18/fastapi-cache/issues/70).**
0.5.0 was published on 2026-11-21. Keep `fastapi_cache` imports, default-key
golden fixtures, Python 3.8–3.10 functional legacy compatibility and the
published Redis client 4.x migration path. **Do not** preserve unsafe
historical response/tenant behavior.

### Required release gates

| Priority | Issue / deliverable | Acceptance |
|---|---|---|
| **Completed** | [#66 security/Dependabot](https://github.com/agustin18/fastapi-cache/issues/66) | Final authenticated delta: 120/120 records, 21 unchanged open, no new/reopened/review-required findings; 7/7 installed profiles; scoped 0.5.0 decision recorded. Historical alerts remain open where applicable |
| **Completed** | [#67 CI reliability](https://github.com/agustin18/fastapi-cache/issues/67) | Closed: docs-only Towncrier positive/negative verification (#71/#76/#77). No softened mandatory tests |
| **Completed / bounded residual** | [#68 generated keys](https://github.com/agustin18/fastapi-cache/issues/68) and [#53 Vary](https://github.com/agustin18/fastapi-cache/issues/53) | #68 closed and published in 0.4.1; #53 opt-in `vary_headers` merged in #81 with returned-Response Vary tests. #53 remains open for application-specific hidden identity/tenant and resource limits |
| **Completed** | [#69 published migration + rollback](https://github.com/agustin18/fastapi-cache/issues/69) | Part A #80 and final Part B #82 passed; **13/13** Phase B jobs on final `stable`, both distributions and legacy rollback. Exact hashes are in the 0.5.0 status record |
| **Completed** | [#66 security](https://github.com/agustin18/fastapi-cache/issues/66) | Fresh final delta, modern installed audits, scope-by-scope risk acceptance and explicit maintainer release decision. Historical 21-alert disposition is not inherited automatically |

### Optional opt-in additions (NOT 0.5.0 release gates)

| Priority | Issue | Acceptance |
|---|---|---|
| **P1** | [#49 exclude_params](https://github.com/agustin18/fastapi-cache/issues/49) | Deterministic named/positional argument handling; never implicitly drop user, tenant or response-defining inputs; old default hash unchanged |
| **P1** | [#54 bounded InMemory](https://github.com/agustin18/fastapi-cache/issues/54) | Optional `max_entries` with eviction/TTL/concurrency tests and benchmark; default unchanged |
| **P1** | [#50 cache observability](https://github.com/agustin18/fastapi-cache/issues/50) | Typed HIT/MISS/BYPASS/STORE/ERROR events, no sensitive keys/payloads, callback exceptions isolated, no mandatory telemetry dependencies |

**Parallel, not 0.5.0 blockers:** [#48 versioned docs site](https://github.com/agustin18/fastapi-cache/issues/48)
and [#51 Python 3.14 research](https://github.com/agustin18/fastapi-cache/issues/51).
User-facing migration/security documentation *is* required; a separately
hosted site is optional. [#45 DynamoDB correctness](https://github.com/agustin18/fastapi-cache/issues/45)
and [#55 MD5/FIPS portability](https://github.com/agustin18/fastapi-cache/issues/55)
remain targeted maintenance candidates, potentially `0.5.x`, after real
reproduction. Python 3.14 must not enter published metadata without a
full compatible matrix.

### Focused PR sequence — current release train

1. **Completed:** #67 docs-only gate (#71/#76/#77) and #68 generated-handler key fix,
   shipped and verified in 0.4.1.
2. **Completed:** #69 Phase A, [PR #80](https://github.com/agustin18/fastapi-cache/pull/80):
   published 0.2.2→0.4.1 goldens, clean installations and Redis 7.4 rollback.
3. **Completed and published:** #53 [PR #81](https://github.com/agustin18/fastapi-cache/pull/81):
   explicit header variation and returned-Response Vary; independent security
   limitations remain tracked in #53.
4. **Completed:** [#82](https://github.com/agustin18/fastapi-cache/pull/82) staged the
   version and exact wheel/sdist Phase-B matrix; [#83](https://github.com/agustin18/fastapi-cache/pull/83)
   completed promotion docs and the changelog. Merge SHA `40c86d5` for the latter.
5. **Completed:** exact-final-SHA Phase B, security profiles and fresh
   Dependabot delta; annotated tag `v0.5.0`, TestPyPI and PyPI publication
   are recorded in [0.5.0 release status](docs/releases/RELEASE_STATUS_0.5.0.md).

The current [release-specific checklist](docs/releases/RELEASE_CANDIDATE_0.5.0.md)
is authoritative for remaining gates. **Optional #49/#54/#50**
are now deferred to a separately reviewed future minor release; none
blocks 0.5.0.

Additional confirmed security or backend bugs warrant their own focused
PRs. Do not artificially expand the scope with distributed locks, tags,
new cluster/failover promises or breaking app-level config. Keep the
0.5.0 release bounded enough for review by a single maintainer. A patch
release does not need to wait for 0.5.0 if a narrowly isolated safety
fix can be shipped with verified compatibility.

## Post-0.5.0 backlog and legacy references

These are candidates, not commitments. New public API work starts from a
focused issue, a privacy/key-compatibility review and tests on the supported
matrix. None of them reopens the published 0.5.0 signoff.

| Priority | Backlog item | Why it is still open |
|---|---|---|
| **P1 — security semantics** | [#53](https://github.com/agustin18/fastapi-cache/issues/53) hidden tenant/identity/context, proxy trust and header-cardinality limits | `vary_headers` is explicit; it is not automatic tenant isolation |
| **P1 — correctness** | [#45](https://github.com/agustin18/fastapi-cache/issues/45) DynamoDB expired-value and client-lifecycle correctness | Experimental backend; needs a real-service reproduction |
| **P1 — portability** | [#55](https://github.com/agustin18/fastapi-cache/issues/55) FIPS/restricted-MD5 key compatibility | Preserve legacy digests on non-FIPS profiles |
| **P2 — API** | [#49](https://github.com/agustin18/fastapi-cache/issues/49) deterministic argument filtering | Must never silently drop identity or response-defining inputs |
| **Source merged, release pending** | [#54 / #85](https://github.com/agustin18/fastapi-cache/pull/85) bounded InMemory | Read-only cap, default unchanged; **not** in 0.5.0 |
| **P2 — observability** | [#50](https://github.com/agustin18/fastapi-cache/issues/50) typed HIT/MISS/BYPASS/STORE/ERROR events | Opt-in, privacy-safe and no mandatory telemetry dependency |
| **P3 — compatibility** | [#51](https://github.com/agustin18/fastapi-cache/issues/51) Python 3.14 qualification | Only after a full functional/security matrix passes |
| **P3 — documentation** | [#48](https://github.com/agustin18/fastapi-cache/issues/48) versioned documentation site | A separately hosted site is optional; migration guides remain authoritative here |

Historical implementation/evidence PRs remain useful references: #32
(disposable migration test), #39 (RC2 publication), #42 (0.3.0 scoped
acceptance), #71/#76/#77 (changelog gate), #73 (factory keys), #74 (0.4.1),
#78 (Dependabot delta), #79 (installed profiles), #80 (Phase A), #81
(vary_headers), #82 (candidate/Phase B) and #83 (promotion/changelog).
Do not reuse their approvals for a different source SHA.

## Defer or research (post-0.5.0)

- **Cache stampede prevention / locks:** local single-flight and
  cross-worker Redis lock design, ownership, TTL, timeouts, cancellation,
  failure recovery, consistency and stress tests. Default **off**.
- **Tag-based invalidation / route invalidation:** safe index cleanup,
  stale writes, Redis expiry and races under concurrent writers.
- **Backend parity:** Memcached real TTL and `clear` contract; DynamoDB
  real-service tests and key invalidation; precise Redis Cluster
  namespace-clear behavior. Do not advertise unimplemented APIs.
- **App-scoped configuration:** explore replacing process-global singleton
  only with a compatibility strategy; a breaking API belongs in a major
  version or a deliberately parallel API.
- **Advanced HTTP:** beyond the prioritized header/Vary security
  investigation [#53](https://github.com/agustin18/fastapi-cache/issues/53),
  study POST opt-in, stale-while-revalidate, cache headers and CDN
  interactions only after explicit threat modeling.

## Capability gaps and objective adoption criteria (2026-11-21)

Assess the library against **application needs and measured behavior**,
not named third-party projects, marketing comparisons or unverifiable
claims of feature/performance/security parity.

| Capability / application need | Current contract | Evidence required to claim readiness | Target |
|---|---|---|---|
| Legacy migration and stable response identity | Published 0.5.0, pinned CI; release candidate in progress | Controlled installed-package integration, ordinary key goldens, selective rollback and secret-safe key changes | 0.6.0 |
| Entry-count limit for one InMemory instance | Source merged in #85, not shipped in 0.5.0 | Real installed 0.6 artifact, TTL/LRU/fuzz/concurrency, 10k/100k scaling and byte-memory caveat | 0.6.0 |
| Auth/private-request isolation | Conservative defaults and opt-in header variation | #53 library vs app ownership decision; independent negative privacy cases | 0.6.0 gate |
| Privacy-safe callbacks | Not implemented | Typed opt-in signal, data minimization, callback isolation and overhead profile | Next feature train |
| Local single-flight on same key | Not implemented | Independent callers, cancellation, exception propagation, nonblocking behavior and cache miss bounds | Next feature train |
| Invalidating related entries | Key/namespace only | Strict tag/index consistency, TTL cleanup, Redis and local parity, races and bounded work | Later feature train |
| Stale response recovery | Not implemented | Stale bounds, failure/cancellation behavior and HTTP cache-control semantics | Later feature train |
| Multi-app configuration | Process-global settings | Data isolation with independent FastAPI instances, lifespan/reset/concurrency semantics | Design before commitment |
| New Python / Redis client versions | 3.8–3.13 functional, Redis client matrix | New-language CI, typed metadata and installed-distribution vulnerability review | Independently gated |

The next feature train is not part of 0.6.0. Prioritize demonstrable
safety and usefulness on both newly created and migrated services;
exclude broad distributed locking, arbitrary parameter omission,
stale serving, tag invalidation and automatic tenant inference from
a release until their specific tests and threat models pass.

The released upstream `fastapi-cache2==0.2.2` used redis-py 4.x.
This fork's published 0.4.x/0.5.0 artifacts support a broader
Python-conditional Redis client range; unshipped source and Redis
**server** versions alone do not prove redis-py **client** compatibility.

## Continuous security, compatibility and release rules

1. Triage new Dependabot advisories by exact package, version, Python
   profile, runtime path and application/backend control. The 21
   previously scoped open GHSA remain documented historical acceptance
   for **0.3.x**, not promises about new vulnerabilities or consumers.
2. Investigate removal of truly unused dependencies and patched modern
   transitive versions. Track security impact **per installed runtime
   profile**, not by the global count of lockfile alerts.
3. Require functional CI, type/lint checks, Redis integration where
   relevant, publishable wheel/sdist, clean installs, `pip check`,
   and applicable package-audit evidence for every release. Test a
   controlled installed-package integration and rollback path for migration-sensitive changes.
4. Keep authenticated bypass safe by default; `PickleCoder` must not
   receive untrusted cache data. Preserve privacy tests and avoid
   logging secrets or full cache keys.
5. Document default-behavior changes in [MIGRATION.md](MIGRATION.md),
   publish API and installed Python/dependency bounds before declaring
   new support. An issue is not a shipped feature.

## Proposed PR order

Use the [post-0.5.0 backlog](#post-050-backlog-and-legacy-references) for
the next focused PRs. Handle any proven #53 privacy defect immediately;
preserve the 0.5.0 migration contract until a deliberately opt-in key
migration is tested. Investigate #45/#55 in standalone maintenance PRs;
do not block security remediation waiting for feature work.

A final change log, tested distribution and tagged release are needed
for **each new published version**, but are **not a reason to re-open
completed release signoffs**.

# Roadmap — fastapi-cache-stable

**Current published release:** [0.5.0](https://pypi.org/project/fastapi-cache-stable/0.5.0/)
on **2026-11-21**. It includes the factory/wrapped-handler key isolation
from 0.4.1 and opt-in `vary_headers`. See
[0.5.0 release evidence](docs/releases/RELEASE_STATUS_0.5.0.md).
**0.4.1** remains the previous published patch line. Source version and
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


## 0.6.0 — planning, not a release commitment

The active [0.6.0 tracker #86](https://github.com/agustin18/fastapi-cache/issues/86)
supersedes the **completed** [0.5.0 train #70](https://github.com/agustin18/fastapi-cache/issues/70).
[PR #85](https://github.com/agustin18/fastapi-cache/pull/85)
for opt-in bounded InMemory (#54) **merged into `stable`** at commit
`190d105915972d436ddbf4ad152ad654a4db392a`. Its positive integer
`max_entries` cap is **read-only after construction**, counts entries
per instance (not bytes), and retains the default unbounded behavior.
**Not available in the immutable published 0.5.0 wheel.**
The [quickstart](docs/QUICKSTART.md) and
[navigable site source](site_docs/index.md) describe the published release
separately. Pages activation and versioned historical hosting still need
explicit approval and URL verification.

0.6.0 should focus on the merged opt-in bounded InMemory feature,
release validation and the remaining #53 privacy/security disposition.
**Defer #50 observability to 0.7.0 by default** unless fully implemented,
audited and explicitly accepted before freeze. Single-flight is
**research**, and #49 argument filtering requires a separate safety contract.
Proven #53 privacy defects outrank the feature roadmap. Never inherit
0.5.0's release-specific security acceptance for a different SHA.


## Adoption and competitive documentation (0.6.0 proposal)

- [#88](https://github.com/agustin18/fastapi-cache/issues/88):
  **first coordinated public promotion**, not the first PyPI release;
  published 0.5.0 stays the baseline until a separate reviewed 0.6.0.
- [#48](https://github.com/agustin18/fastapi-cache/issues/48):
  navigable Zensical docs shipped in #87 and manual-only GitHub Pages
  workflow, API reference and comparison guide merged in #89. Public
  activation, stable-only environment restriction and live URL verification
  require separate approval.
- [Capability selection guide](site_docs/reference/alternatives.md):
  explain the shipped contract, unmet needs and acceptance evidence
  without nominal comparisons or unverified superiority claims.
- [Public API guide](site_docs/reference/api.md):
  distinguish *published 0.5.0* from merged-but-unreleased
  `max_entries` in the next-release source.
- **Feature freeze:** #54/#85 passed independent counteraudit and exact-head
  CI before merge; **final 0.6.0 artifacts require new security and
  migration evidence**. #50 is deferred to 0.7.0 unless separately approved.
  #53 residual remains a security risk-disposition gate; #91 requires two
  independent consumers; #92 tracks final candidate checks and manual
  release approval. #49, tags and single-flight remain future research.

## Version strategy

- **0.5.x:** current published line. Keep the published Python
  `>=3.8,<3.14` metadata and documented Redis client ranges; security
  maintenance is best-effort on server-side CPython 3.11–3.13.
- **0.4.x:** previous published patch line, retained for migration.
- **0.6.0 candidate:** bounded InMemory is merged in source only, not
  in the published 0.5.0 distribution. Argument filtering (#49) and
  privacy-safe event callbacks (#50) remain separate possible future work.
  A new minor release needs a reviewed wheel/sdist, not a retroactive
  rewrite of 0.5.0.
  Keep distributed locking, tag invalidation and app-scoped configurations
  in research until their concurrency and privacy contracts are tested.
- **1.0.0:** not automatically scheduled; current
  [support policy](SUPPORT.md) requires a co-maintainer before committing
  to a longer `1.x` support window.

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
stays open **only for residual arbitrary hidden context/tenant identity,
proxy trust and header cardinality**. Neither explicit-`Request`
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
| Legacy migration and stable response identity | Published 0.5.0, pinned CI; release candidate in progress | Real app installations, ordinary key goldens, selective rollback and secret-safe key changes | 0.6.0 |
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
   consumer and rollback path for migration-sensitive changes.
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

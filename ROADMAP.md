# Roadmap — fastapi-cache-stable

**Historical published baseline:** [0.4.1](https://pypi.org/project/fastapi-cache-stable/0.4.1/)
on **2026-11-20**. The 0.4.1 patch includes the factory/wrapped-handler
key isolation; see [0.4.1 release evidence](docs/releases/RELEASE_STATUS_0.4.1.md).
Consult [PyPI](https://pypi.org/project/fastapi-cache-stable/) for
currently published releases; source version and merged PRs alone do
not imply publication.
**Do not reopen a completed publication gate without new material evidence.**

**0.5.0 preparation record (2026-11-20):** #67 and #68 closed;
#69 Phase A completed in [#80](https://github.com/agustin18/fastapi-cache/pull/80).
#53's explicit `vary_headers` contract merged in
[#81](https://github.com/agustin18/fastapi-cache/pull/81), with residual
hidden tenant/context risks tracked separately. Candidate
[#82](https://github.com/agustin18/fastapi-cache/pull/82) merged as
`6a557eb3` after a 71-check green PR and 13/13 Phase B build/migration jobs.
**Those PR-HEAD tests are historical candidate evidence, not approval
of the final published artifacts.** Final promotion SHA revalidation,
release-specific security [#66](https://github.com/agustin18/fastapi-cache/issues/66)
and [#69](https://github.com/agustin18/fastapi-cache/issues/69) exact wheel/sdist
signoff remain mandatory for publication. See the
[release gate record](docs/releases/RELEASE_CANDIDATE_0.5.0.md).

Everything below is a **candidate plan, not a delivery promise**.
The primary product advantage remains conservative migration from
`fastapi-cache2==0.2.2`, preserved `fastapi_cache` imports, predictable
cache keys and safe default HTTP/private-response behavior.

## Version strategy

- **0.4.x:** backward-compatible maintenance. Keep the published
  Python `>=3.8,<3.14` metadata and documented Redis client ranges;
  security maintenance is best-effort on server-side CPython 3.11–3.13.
- **0.5.0 candidate:** consolidate already merged factory-route fix,
  explicit opt-in `vary_headers`, verified legacy migration and exact
  supported-modern security audits. The remaining scope is **Phase B and
  release-scoped #66**, without unrelated features. No tag/publication
  before the final SHA is independently reviewed.
- **Future version (separate opt-in features):** argument filtering,
  bounded InMemory and privacy-safe cache events are optional.
  If they change the public API, prefer a separately reviewed new
  minor release (e.g. `0.6.0`) instead of delaying or expanding 0.5.0.
  Keep distributed locking, tags and app-scoped configurations in research.
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
[docs/releases](docs/releases/). Published 0.4.1 resolves #68's generated
route replay, while source `stable` after #81 implements explicit opt-in
HTTP `Vary` (not in published 0.4.1). [#53](https://github.com/agustin18/fastapi-cache/issues/53)
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
| **Delivered in source after 0.4.1** | [#53: Vary opt-in and residual](https://github.com/agustin18/fastapi-cache/issues/53) | PR #81 merged: explicit hashed `:vary-v1:` with returned Response `Vary` on MISS/HIT/304. **Not in published 0.4.1**; issue stays open for hidden identity/tenant/proxy/cardinality limits |
| **P2 — conditional** | [#51: Python 3.14 qualification](https://github.com/agustin18/fastapi-cache/issues/51) | Full functional/security matrix must pass before changing metadata; otherwise stay out of range |

A `0.4.x` release is **not mandatory for docs-only or CI-only merges**;
batch a small, regression-tested fix and publish only when there is
user-facing value. Do not change cache keys or the Python/Redis metadata
ranges without a verified compatibility lane.

## 0.5.0 — secure, tested modern drop-in

**Release tracker: [#70](https://github.com/agustin18/fastapi-cache/issues/70).**
This is a proposed scope, not a schedule or permission to publish. Keep
`fastapi_cache` imports, default-key golden fixtures, Python 3.8–3.10
functional legacy compatibility and the published Redis client 4.x migration
path. **Do not** preserve unsafe historical response/tenant behavior.

### Required release gates

| Priority | Issue / deliverable | Acceptance |
|---|---|---|
| **P0** | [#66 security/Dependabot](https://github.com/agustin18/fastapi-cache/issues/66) | **Reuse** authenticated 0.4.0 baseline: 120 historical/current records, 21 unchanged open, no new material findings. Run existing scheduled/manual delta closer to 0.5.0; triage changed alerts, patch reachable modern profiles and exact-wheel `pip-audit`. Legacy-only alerts not silently dismissed |
| **Completed** | [#67 CI reliability](https://github.com/agustin18/fastapi-cache/issues/67) | Closed: docs-only Towncrier positive/negative verification (#71/#76/#77). No softened mandatory tests |
| **Completed / bounded residual** | [#68 generated keys](https://github.com/agustin18/fastapi-cache/issues/68) and [#53 Vary](https://github.com/agustin18/fastapi-cache/issues/53) | #68 closed and published in 0.4.1; #53 opt-in `vary_headers` merged in #81 with returned-Response Vary tests. #53 remains open for application-specific hidden identity/tenant and resource limits |
| **P0 — pending final SHA** | [#69 published migration + rollback](https://github.com/agustin18/fastapi-cache/issues/69) | Part A #80 and candidate Part B #82 merged; **13/13** Phase B candidate jobs passed, including both distributions and legacy rollback. Re-run on final release-intended stable SHA after promotion and archive exact wheel/sdist hashes |
| **P0 — pending final signoff** | [#66 security](https://github.com/agustin18/fastapi-cache/issues/66) | A historical 120-record/21-open baseline is not consent for 0.5.0. Fresh authenticated delta, final modern installed wheel/sdist scan, scope-by-scope risk acceptance and explicit release decision |

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
remain targeted maintenance candidates, potentially `0.4.x`, after real
reproduction. Python 3.14 must not enter published metadata without a
full compatible matrix.

### Focused PR sequence — current release train

1. **Completed:** #67 docs-only gate (#71/#76/#77) and #68 generated-handler key fix,
   shipped and verified in 0.4.1.
2. **Completed:** #69 Phase A, [PR #80](https://github.com/agustin18/fastapi-cache/pull/80):
   published 0.2.2→0.4.1 goldens, clean installations and Redis 7.4 rollback.
3. **Completed in source:** #53 [PR #81](https://github.com/agustin18/fastapi-cache/pull/81):
   explicit header variation and returned-Response Vary; independent security
   limitations stay open. Not yet in a published 0.5.0 package.
4. **Merged candidate:** [#82](https://github.com/agustin18/fastapi-cache/pull/82)
   staged version `0.5.0` and the exact wheel/sdist Phase-B migration matrix
   on Python 3.8–3.13, including a real Redis package rollback; all
   candidate checks passed. Merge SHA `6a557eb3`; no tag or publication
   was created by the merge.
5. **Promotion:** complete version-neutral installation, support,
   migration and security text, generate 0.5.0 Towncrier changelog
   and consume its fragments; release documentation must not falsely
   claim live PyPI availability or lack thereof.
6. **Exact final artifacts:** rerun #69 Phase B and #66 modern installed
   wheel/sdist security profiles **after promotion** at the intended
   `stable` SHA. Archive hashes, reports, GitHub run IDs, dependency
   metadata and independent consumer evidence.
7. **Manual release decision:** fresh authenticated Dependabot delta,
   scoped #66 security acceptance and #69 final migration signoff;
   then an **explicitly approved** annotated tag, TestPyPI/PyPI and
   provenance record, with no automatic publication.

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

## Defer or research (post-0.4.0)

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

## Competitor feature map (source-code/docs snapshot 2026-11-19)

This is **not** a performance ranking; advertised features are not
independently benchmarked here.

| Library | Verified positioning | Gap / decision for our fork |
|---|---|---|
| [Yolley/fastapi-cache](https://github.com/Yolley/fastapi-cache) (`fastapi-cache2-fork` 2.3.0) | Uses the same `fastapi_cache` import, requires Python 3.11+, Redis client `>=5,<8`, optional `with_lock` | Redis modernization is immediate; lock support can follow after concurrency tests |
| [FastAPI-CacheX](https://github.com/allen0099/FastAPI-CacheX) (0.6.2) | Separate `fastapi_cachex` API; HTTP cache, app cache, tags, stale responses, locks, metrics hooks and structured docs | Borrow quality of docs/tests and opt-in ergonomics, **not** an incompatible rewrite |
| [Redis FastAPI SDK](https://github.com/redis/fastapi-redis-sdk) (0.10.0) | Redis-maintained SDK, redis-py `>=6`, includes Redis-related session/rate-limiting/telemetry functions | Compete on low-friction `fastapi-cache2` migration, not on having every Redis integration |

The released upstream [`fastapi-cache2==0.2.2`](https://pypi.org/project/fastapi-cache2/0.2.2/)
used redis-py **4.x**; the published `fastapi-cache-stable` 0.4.x line extends client support conditionally.
An upstream **unreleased** main branch used redis-py 5.x; neither
unreleased source nor Redis **server** major versions prove support
for a redis-py client major.

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

Follow [the release-gates-first 0.5.0 PR sequence](#focused-pr-sequence--release-gates-first-features-parallel).
Handle any proven #53/#68 privacy defect immediately; preserve the
0.4.x migration contract until a deliberately opt-in key migration is tested.
Investigate #45/#55 in standalone maintenance PRs; do not block #66
security remediation waiting for feature work.

A final change log, tested distribution and tagged release are needed
for **each new published version**, but are **not a reason to re-open
completed release signoffs**.

# Roadmap — fastapi-cache-stable

**Published baseline:** [0.4.1](https://pypi.org/project/fastapi-cache-stable/0.4.1/)
on **2026-11-20**. The 0.4.1 patch includes the factory/wrapped-handler key
isolation; see [0.4.1 release status](docs/releases/RELEASE_STATUS_0.4.1.md)
for publication evidence. The 0.4.0 release remains the previous baseline. The `0.3.x` artifacts remain the previous migration line.
**Do not reopen a completed publication gate without new material evidence.**

Everything below is a **candidate plan, not a delivery promise**.
The primary product advantage remains conservative migration from
`fastapi-cache2==0.2.2`, preserved `fastapi_cache` imports, predictable
cache keys and safe default HTTP/private-response behavior.

## Version strategy

- **0.4.x:** backward-compatible maintenance. Keep the published
  Python `>=3.8,<3.14` metadata and documented Redis client ranges;
  security maintenance is best-effort on server-side CPython 3.11–3.13.
- **0.5.0:** release-quality security/CI, confirmed factory-route key-collision
  mitigation, residual tenant/context isolation review and verifiable legacy
  migration. This is enough to justify the release **without feature additions**.
  If a safe targeted 0.4.x correctness fix is ready earlier, release it first.
- **0.5.x later/optional:** opt-in argument filtering, bounded InMemory and
  cache events. Merge into 0.5.0 only if each has its own audited, green PR;
  none may delay a necessary security/correctness release. Keep distributed
  locking, tags and app-scoped configurations in research.
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

`0.3.1` remains the migration baseline and retains its own release history in
[docs/releases](docs/releases/). [#53](https://github.com/agustin18/fastapi-cache/issues/53)
remains open for `Vary`-aware caching, hidden dependency/contextvars/middleware
inputs and per-tenant/user key design. The 0.3.1 explicit-`Request` bypass is
not a general guarantee.

## 0.4.x — maintenance candidates (no release date promised)

| Priority | Focused issue | Deliverable / acceptance |
|---|---|---|
| **P1** | [#55: MD5/FIPS key portability](https://github.com/agustin18/fastapi-cache/issues/55) | Reproduce restricted-hash failures; retain legacy key digests and **Python 3.8** support. Upstream `usedforsecurity=False` needs version-specific handling |
| **P1** | [#45: DynamoDB correctness](https://github.com/agustin18/fastapi-cache/issues/45) | Reproduce/fix expired-value reads and client cleanup lifecycle if verified; keep DynamoDB experimental |
| **P0 — correctness** | [#68: confirmed factory-route key collision](https://github.com/agustin18/fastapi-cache/issues/68) | Fixed by #73 and prepared for 0.4.1: generated/wrapped handlers are partitioned, unwrapped module-level keys are unchanged, and old generated entries are not reused. Complete publication/verification; residual #53 limits remain |
| **P0 — security review** | [#53: residual header/Vary design](https://github.com/agustin18/fastapi-cache/issues/53) | Coordinate hidden-request/tenant variants with #68. Keep current 0.3.1/0.4.0 explicit-Request bypass; prioritize proven privacy risks and versioned cache-key migration |
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
| **P0** | [#67 CI reliability](https://github.com/agustin18/fastapi-cache/issues/67) | [#71](https://github.com/agustin18/fastapi-cache/pull/71) **merged** (31/31 checks). Verify the docs-only gate with an actual Markdown-only PR; investigate only post-0.4.0 failures and concrete same-SHA flake evidence. No soft required tests |
| **P0** | [#68 confirmed route collision](https://github.com/agustin18/fastapi-cache/issues/68) + [#53 context/Vary](https://github.com/agustin18/fastapi-cache/issues/53) | **Incorrect response replay is confirmed**: /a MISS then /b HIT serving /a data, per maintainer agent; independent builder collision reproduced. Commit an HTTP/Redis test, assess tenant/privacy reachability privately if applicable, and fix before optional features. Preserve default key goldens unless a deliberate, documented versioned migration is chosen |
| **P0** | [#69 tested legacy migration and rollback](https://github.com/agustin18/fastapi-cache/issues/69) | **Two reviewable PRs**: (A) immutable old-package goldens, clean install and real Redis/InMemory migration; (B) exact 0.5.0 wheel/sdist, independent consumer, Redis-py 4 fallback and rollback. Deliberately changed security defaults documented |

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

### Focused PR sequence — release gates first, features parallel

1. **Completed:** [#71](https://github.com/agustin18/fastapi-cache/pull/71) fix docs-only Towncrier false gate and add regression coverage; squash merge `f9b12aa`. Validate against a docs-only PR (this PR).
2. **Highest priority:** [#68](https://github.com/agustin18/fastapi-cache/issues/68) confirmed cross-route wrong response, with [#53](https://github.com/agustin18/fastapi-cache/issues/53) hidden-context/privacy review. One focused reproduction PR and a separate minimal patch PR; **ship a compatible 0.4.x correction early if justified**. No global key-format migration without a user-visible rollout/rollback strategy.
3. [#66](https://github.com/agustin18/fastapi-cache/issues/66) reuse the authenticated pre-0.4.0 120/21 baseline and run a fresh delta; separate dependency remediations and exact-profile security audit.
4. [#67](https://github.com/agustin18/fastapi-cache/issues/67) review CI failures since 0.4.0 or documented same-SHA repeats only; no broad 100–300-run retrospective unless evidence demands it.
5. [#69](https://github.com/agustin18/fastapi-cache/issues/69) Part A: immutable upstream 0.2.2 golden-key/HTTP behavior and clean installation comparison.
6. [#69](https://github.com/agustin18/fastapi-cache/issues/69) Part B: exact 0.5.0 candidate wheel/sdist, independent consumer and rollback evidence after version bump.
7. Final release PR: merge-quality code, release-shaped CI, scoped Dependabot risk audit, immutable distribution evidence and **separate approval** for tag/TestPyPI/PyPI.

**Optional independent PRs:** [#49](https://github.com/agustin18/fastapi-cache/issues/49), [#54](https://github.com/agustin18/fastapi-cache/issues/54), [#50](https://github.com/agustin18/fastapi-cache/issues/50); these can ship in 0.5.0 if completed safely in time, or in a later 0.5.x/minor release without blocking security/correctness.

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

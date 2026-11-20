# Roadmap — fastapi-cache-stable

**Published baseline:** [0.4.0](https://pypi.org/project/fastapi-cache-stable/0.4.0/)
on **2026-11-20**. The `v0.4.0` tag points at the verified release commit;
see [0.4.0 release status](docs/releases/RELEASE_STATUS_0.4.0.md) for artifact
hashes and evidence. The `0.3.x` artifacts remain the previous migration line.
**Do not reopen a completed publication gate without new material evidence.**

Everything below is a **candidate plan, not a delivery promise**.
The primary product advantage remains conservative migration from
`fastapi-cache2==0.2.2`, preserved `fastapi_cache` imports, predictable
cache keys and safe default HTTP/private-response behavior.

## Version strategy

- **0.4.x:** backward-compatible maintenance. Keep the published
  Python `>=3.8,<3.14` metadata and documented Redis client ranges;
  security maintenance is best-effort on server-side CPython 3.11–3.13.
- **0.5.x:** concurrency-heavy and usability features after evidence of
  user demand: observability, bounded InMemory, cache-stampede protection,
  tag invalidation, app-scoped configuration and versioned documentation.
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
| **P1 — security** | [#53: residual header/Vary design](https://github.com/agustin18/fastapi-cache/issues/53) | Design opt-in header variation and hidden-context guidance with key/namespace migration; prioritize any confirmed isolation defect |
| **P2 — conditional** | [#51: Python 3.14 qualification](https://github.com/agustin18/fastapi-cache/issues/51) | Full functional/security matrix must pass before changing metadata; otherwise stay out of range |

A `0.4.x` release is **not mandatory for docs-only or CI-only merges**;
batch a small, regression-tested fix and publish only when there is
user-facing value. Do not change cache keys or the Python/Redis metadata
ranges without a verified compatibility lane.

## 0.5.x — capabilities and ergonomics

| Priority | Issue | Done when |
|---|---|---|
| **P1** | [#50: opt-in observability](https://github.com/agustin18/fastapi-cache/issues/50) | HIT/MISS/BYPASS/store/error events usable without mandatory metrics dependencies; no key or payload leakage |
| **P1** | [#54: bounded InMemory](https://github.com/agustin18/fastapi-cache/issues/54) | Opt-in capacity and eviction policy with expiration, isolation and concurrency tests |
| **P2** | [#49: safe exclude_params](https://github.com/agustin18/fastapi-cache/issues/49) | Explicit opt-in; deterministic-key/PYTHONHASHSEED tests; never excludes tenant or user identity by default |
| **P2** | [#48: versioned documentation site](https://github.com/agustin18/fastapi-cache/issues/48) | Build/link checks; Redis, InMemory, safe-auth and migration examples exercised in CI |
| **Research** | Cache stampede, tag invalidation, app-scoped configuration | Ownership, TTL, cancellation, consistency and rollback semantics proven before defaults change |

**Keep the next release bounded:** verified correctness and compatibility
justify a release on their own. Do not delay a security/correctness fix for
unrelated feature work.

## Defer or research (post-0.4.0)

- **Cache stampede prevention / locks:** local single-flight and
  cross-worker Redis lock design, ownership, TTL, timeouts, cancellation,
  failure recovery, consistency and stress tests. Default **off**.
- **Tag-based invalidation / route invalidation:** safe index cleanup,
  stale writes, Redis expiry and races under concurrent writers.
- **Backend parity:** Memcached real TTL and `clear` contract; DynamoDB
  real-service tests and key invalidation; precise Redis Cluster
  namespace-clear behavior. Do not advertise unimplemented APIs.
- [#54: InMemory capacity/eviction](https://github.com/agustin18/fastapi-cache/issues/54):
  bounded opt-in store with verified expiration, eviction and isolation.
  Current store has no size cap.
- **App-scoped configuration:** explore replacing process-global singleton
  only with a compatibility strategy; a breaking API belongs in a major
  version or a deliberately parallel API.
- **Observability:** [#50](https://github.com/agustin18/fastapi-cache/issues/50)
  is now **0.5.x preferred**; an isolated opt-in implementation can ship
  earlier only if it does not delay #47.
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

**0.4.x maintenance:** #55 (FIPS portability if compatible) → #45
(tested experimental backend fixes) → #53 residual header/variation design.
Batch small fixes into a patch release only if useful to users.

**0.5.x:** #50 (observability), #54 (bounded InMemory), #49
(exclude_params), #48 (versioned documentation site), config-per-app,
cache stampede locks and tag invalidation, subject to user demand and
concurrency/security tests.

A final change log, tested distribution and tagged release are needed
for **each new published version**, but are **not a reason to re-open
completed release signoffs**.

# Roadmap — fastapi-cache-stable

**Published baseline:** [0.3.0](https://pypi.org/project/fastapi-cache-stable/0.3.0/)
on **2026-11-19**.
The annotated `v0.3.0` tag resolves to
`c1b83036a4d3900432a96a44686cf6dd56cf8618`.
See [release status](RELEASE_STATUS_0.3.0.md) for the final artifact
hashes and evidence. **0.3.0 is finished; do not reopen publication gates
for already accepted risks without new material evidence.**

Everything below is a **candidate plan, not a delivery promise**.
The primary product advantage remains conservative migration from
`fastapi-cache2==0.2.2`, preserved `fastapi_cache` imports, predictable
cache keys and safe default HTTP/private-response behavior.

## Version strategy

- **0.3.x:** backward-compatible patches, documentation, packaging
  hygiene and demonstrated correctness/security fixes. Keep the released
  Python `>=3.8,<3.14` and documented functional legacy contract;
  security maintenance is best-effort on server-side CPython 3.11–3.13.
- **0.4.0:** optional/additive capabilities **after tests**, especially
  modern redis-py. Do not silently change default keys, JSON serialization,
  anonymous MISS/HIT behavior or authenticated bypass.
- **0.5.x / later:** concurrency-heavy features, tag invalidation and
  expanded backends if there is evidence of user demand and clear
  failure/rollback semantics.
- **1.0.0:** not automatically scheduled; current
  [support policy](SUPPORT.md) requires a co-maintainer before committing
  to a longer `1.x` support window.

## 0.3.1 — maintenance and adoption (no release date promised)

| Order | Focused PR / issue | Deliverable / acceptance |
|---|---|---|
| **P0** | This post-release documentation PR | Remove false "0.3.0 not published" messages; add [quickstart](docs/QUICKSTART.md) and provenance; keep historical GHSA evidence immutable |
| **P1** | [#44: mandatory dependencies](https://github.com/agustin18/fastapi-cache/issues/44) | Check `uvicorn`/`jinja2` runtime reachability, wheel metadata and clean installs; trim **only if** verified compatible; quantify dependency-graph reduction |
| **P1** | [#46: security delta monitoring](https://github.com/agustin18/fastapi-cache/issues/46) | Repeatable **new/reopened/changed GHSA** comparison split by modern runtime, legacy test and application-owned risks; no blanket dismissal of 21 accepted alerts |
| **P2** | [#45: DynamoDB correctness](https://github.com/agustin18/fastapi-cache/issues/45) | Reproduce/fix expired-value reads and client cleanup lifecycle if verified; keep DynamoDB experimental and defer parity without real integration |
| **P2** | [#48: documentation site](https://github.com/agustin18/fastapi-cache/issues/48), first stage | Structure install/migration, examples and public API reference; a full hosted docs site can follow in 0.4.0 |

A `0.3.1` release is **not mandatory for docs-only merges**; batch a
small, regression-tested improvement and publish only when there is
user-facing value. Any patch that modifies requirements must pass
**clean wheel installs**, the Python matrix and a real consumer smoke
before release. Do not change cache key format or the 0.3.x Python
install range in a patch.

## 0.4.0 — modern compatibility and opt-in ergonomics

| Priority | PR / issue | Done when |
|---|---|---|
| **P0 — release driver** | [#47: redis-py 5/6/7, research 8](https://github.com/agustin18/fastapi-cache/issues/47) | Tests with **real Redis** exercise GET, SET, TTL, pipelining, SCAN/UNLINK, clear boundaries, binary values, error paths and MISS→HIT. The published 4.6 migration lane remains working if technically possible. Widen redis extra only for versions actually tested |
| **P1 — optional** | [#51: Python 3.14 qualification](https://github.com/agustin18/fastapi-cache/issues/51) | Full compatibility and security matrix succeeds; if not, keep metadata unchanged and record blockers. No EOL interpreter drop solely to improve Dependabot counts |
| **P1 — optional** | [#49: safe exclude_params](https://github.com/agustin18/fastapi-cache/issues/49) | Explicit opt-in, stable legacy keys when unset, privacy/tenant identity guard tests, documented key migration |
| **P2 — stretch** | [#50: HIT/MISS/BYPASS/ERROR events](https://github.com/agustin18/fastapi-cache/issues/50) | Hook failures isolated; no raw keys, cookie/token/user data by default; no mandatory telemetry dependencies |
| **P2 — documentation** | [#48: tested docs site](https://github.com/agustin18/fastapi-cache/issues/48) | Build/link checks; Redis, InMemory, safe-auth and migration examples exercised in CI |

**Keep 0.4.0 bounded:** redis-py compatibility and a documented tested
matrix justify the release on their own. If Python 3.14, safe key
configuration or observability is not ready, move it to 0.4.1/0.5.x.
No reason to delay verified Redis support for unrelated features.

## Defer or research (post-0.4.0)

- **Cache stampede prevention / locks:** local single-flight and
  cross-worker Redis lock design, ownership, TTL, timeouts, cancellation,
  failure recovery, consistency and stress tests. Default **off**.
- **Tag-based invalidation / route invalidation:** safe index cleanup,
  stale writes, Redis expiry and races under concurrent writers.
- **Backend parity:** Memcached real TTL and `clear` contract; DynamoDB
  real-service tests and key invalidation; precise Redis Cluster
  namespace-clear behavior. Do not advertise unimplemented APIs.
- **InMemory capacity/eviction:** bounded optional store with verified
  expiration and isolation. Current store has no size cap.
- **App-scoped configuration:** explore replacing process-global singleton
  only with a compatibility strategy; a breaking API belongs in a major
  version or a deliberately parallel API.
- **Advanced HTTP:** `Vary`, POST opt-in, stale-while-revalidate, HTTP
  privacy model and CDN interactions only after explicit threat modeling.

## Competitor feature map (source-code/docs snapshot 2026-11-19)

This is **not** a performance ranking; advertised features are not
independently benchmarked here.

| Library | Verified positioning | Gap / decision for our fork |
|---|---|---|
| [Yolley/fastapi-cache](https://github.com/Yolley/fastapi-cache) (`fastapi-cache2-fork` 2.3.0) | Uses the same `fastapi_cache` import, requires Python 3.11+, Redis client `>=5,<8`, optional `with_lock` | Redis modernization is immediate; lock support can follow after concurrency tests |
| [FastAPI-CacheX](https://github.com/allen0099/FastAPI-CacheX) (0.6.2) | Separate `fastapi_cachex` API; HTTP cache, app cache, tags, stale responses, locks, metrics hooks and structured docs | Borrow quality of docs/tests and opt-in ergonomics, **not** an incompatible rewrite |
| [Redis FastAPI SDK](https://github.com/redis/fastapi-redis-sdk) (0.10.0) | Redis-maintained SDK, redis-py `>=6`, includes Redis-related session/rate-limiting/telemetry functions | Compete on low-friction `fastapi-cache2` migration, not on having every Redis integration |

The released upstream [`fastapi-cache2==0.2.2`](https://pypi.org/project/fastapi-cache2/0.2.2/)
used redis-py **4.x**, like `fastapi-cache-stable==0.3.0`.
An upstream **unreleased** main branch used redis-py 5.x; neither
unreleased source nor Redis **server** major versions prove support
for a redis-py client major.

## Continuous security, compatibility and release rules

1. Triage new Dependabot advisories by exact package, version, Python
   profile, runtime path and application/backend control. The 21
   previously scoped open GHSA remain documented historical acceptance
   for **0.3.0**, not promises about new vulnerabilities or consumers.
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

**0.3.1 candidates:** this docs/provenance PR → #44 (dependency audit)
→ #46 (GHSA delta workflow) → #45 (minimal tested backend correctness).

**0.4.0 candidates:** #47 (redis-py) → #51 (Python 3.14 assessment)
→ #49 (safe keys, only if ready) → #50 (observability, stretch)
+ #48 (documentation site in independent documentation PRs).

A final change log, tested distribution and tagged release are needed
for **each new published version**, but are **not a reason to re-open
0.3.0 release signoff**.

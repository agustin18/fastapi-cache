# Competitive roadmap: fastapi-cache-stable 0.8–1.0

**Research snapshot: 2026-11-23. Proposal, not shipped behavior.**
Baseline at the time of research: the public package
`fastapi-cache-stable==0.6.0`; development source `0.7.0.dev0`.
CacheX's PyPI version `0.7.3` is dated **2026-11-23**;
`cashews==7.6.0` was released in September 2026;
`aiocache==0.12.3` in September 2024. The official
`fastapi-redis-sdk` is a **Redis-specific** FastAPI SDK (Python 3.10+,
Redis 7.4+). These are different product scopes: do not turn a feature
matrix into a claim that they have equal implementations, security
models or speed.

## Positioning: what to win, what not to chase

The **wedge** is compatibility: keeping `fastapi_cache` imports,
ordinary cache keys, Python 3.8–3.10 functional legacy where supported,
tested migration/rollback from `fastapi-cache2==0.2.2`, credential-aware
HTTP caching and unusually honest security boundaries.

Modern users also expect *ergonomic primitives*, not only cache
decorators. The roadmap therefore targets: lifecycle-isolated apps,
predictable concurrency, invalidation, minimal observability,
safe corruption handling and maintenance-quality docs. It does **not**
aim to reimplement all of cashews, promise cluster/failover, or market
unreproduced superiority in 1–2 versions.

## Current competitor capabilities, grounded in official docs

| Product | Differentiation documented as of snapshot | Honest current gap/opportunity |
|---|---|---|
| [FastAPI-CacheX 0.7.3](https://pypi.org/project/fastapi-cachex/0.7.3/) | [HTTP cache](https://fastapi-cachex.readthedocs.io/en/stable/HTTP_CACHING/) with tags, stale, coalescing and client directives; [application cache](https://fastapi-cachex.readthedocs.io/en/stable/APP_CACHE/), event hooks, Memcached/Redis, [distributed locks](https://fastapi-cachex.readthedocs.io/en/stable/) | We currently lack these integrated features; choose safe, smaller opt-in subsets without sacrificing drop-in stability |
| [cashews 7.6.0](https://pypi.org/project/cashews/) | Async function-cache toolkit, early/soft refresh, tags, lock strategies, Redis client-side caching, disk cache, Prometheus and rate limiting | Do **not** chase unrelated rate limiting/Bloom/circuit breakers; validate need for cache- and HTTP-specific concurrency and refresh |
| [aiocache 0.12.3](https://pypi.org/project/aiocache/) | Generic async decorators, plugin hooks/metrics, serializer/backends and [locking](https://aiocache.aio-libs.org/en/stable/) | FastAPI/HTTP correctness is our domain; interoperability and minimal metrics are opportunities |
| [official FastAPI Redis SDK](https://redis.github.io/fastapi-redis-sdk/) | Lifespan integration, dependency-based caching/eviction and explicit [OTel](https://redis.github.io/fastapi-redis-sdk/latest/guide/configuration/) with a Redis-first architecture | Offer safe optional Redis integrations without forcing Redis, OTel or Python 3.10+ in core |
| [fastapi-cache2](https://pypi.org/project/fastapi-cache2/) | Familiar import/decorator API and historical keys | Our migration compatibility is the entry point; preserve it except for independently justified bug/security fixes |

This is a documentation-sourced **capability inventory**, not verified
feature-parity tests or comparative performance. Recheck competitor
versions and exact semantics at each new minor release. In particular,
FastAPI-CacheX's broad feature list is **not** a reason to introduce
silent changes to `@cache` or global initialization.

## Milestone 0.7: qualify and ship small quality delta

**Scope intentionally frozen:** inclusive InMemory deadline (#123);
corrupt-entry decode before ETag/304 (#124); Redis tuple contract (#114).
Error/ownership tests (#131), real Redis **no-retry** daemon-fault
tests (#133), benchmarks and release tooling are validation rather
than new runtime behavior. #130/#132 keep 0.7 dev source and
wheel-hash socket harness separate from published 0.6.0.

Release conditions: source/version/changelog/docs consistency,
security/privacy/correctness risk dispositions (#53/#111/#112);
permitted #100 no-performance-claim deferral **only after express
reviewer and maintainer acceptance**; 12 Redis rollback + 7 installed
security + 1 build job, all **20** first-attempt Phase B; exact
wheel/sdist hashes; independent final-artifact GO; separate tag and
registry permissions. No new feature/HA/p99 claims.

## Milestone 0.8.0: app-safe competitive primitives

### A. Context and lifecycle (#99), the architectural prerequisite

- Define a *new opt-in* app-scoped context that does not mutate default
  process-global `FastAPICache` behavior. Key builder, coder,
  backend, prefix and ownership are explicit. No silent new global
  policy or unreviewed default key change.
- Negative test **two FastAPI apps in one process**, both with
  different authentication and tenant data, simultaneous lifespans,
  both orders of shutdown, request tasks during shutdown, workers/
  event loops where feasible, borrower-vs-owner Redis connection.
- Prove that values and callbacks do not cross apps. Document
  application-managed identity still required *within* a single app.
- Pilot migration of one normal installed-wheel consumer with old API
  intact, then independent privacy review. No immediate API promise
  until design passes and tests reproduce a safe lifecycle.

### B. Local per-key single-flight (#96)

- Disabled by default; match only fully validated keys **within
  one app context**. No distributed lock disguised as local lock.
- Bound maximum inflight entries/waiters, wait timeout and per-key
  lifecycle; use no unbounded background work or sensitive key logs.
- Distinguish creator, waiter and app-shutdown cancellation, encoder
  failures and Redis read/write errors. Invalidation during refresh
  must not resurrect stale data. Keep HTTP 304/Cache-Control/Vary safe.
- Measure 1k+ contended same-key callers, duplicate handler executions,
  p50/p95/p99, CPU/RSS and fairness ON vs OFF using installed wheel,
  independent controlled host **before speed claims**.

### C. Minimal typed cache events (#50)

- Optional, schema-versioned HIT/MISS/BYPASS/STORE/ERROR with reason,
  backend type and bounded coarse elapsed time **without** keys, raw
  URLs/query strings, auth headers, payloads, tenant IDs, or exception
  text; avoid high-cardinality metrics labels by default.
- Sync/async callback failure isolation; task lifetime and event-loop
  ownership; no telemetry dependency, no forced exporter.
- Stress tests for callback reentrance, failure and cancellation.
  Demonstrate measurable disabled-default overhead and no new public
  leakage channels.

### D. Failure policy (#112), selected and explicit

- Only bounded, recognized corruption recovery may opt in; default
  fail-closed decode remains, no automatic Pickle on untrusted bytes.
- For backend GET/SET failures specify representation/ETag and retry
  semantics separately. Error policy must be scoped to app ownership,
  not a second hidden process-global singleton.
- FastAPI auth/tenant, cache-control and invalidation races are
  mandatory before declaring these features production-capable.

**0.8 GO** requires the above threat models, real Redis and
InMemory negative tests, installed wheel migration and explicit
default-off behavior. A blocker can defer a feature to 0.8.x
rather than delaying safe unrelated fixes.

## Milestone 0.9.0: invalidation, application values and HTTP depth

### Tags (#97) and invalidation

- TTL-consistent local/Redis indexes; avoid orphan unbounded
  tag sets, whole-database scans, CLUSTER namespace-clear fantasies.
- Handle invalidate-while-compute, concurrent add/delete, expiry,
  clear(namespace), tombstones/versioned tags and cross-worker
  consistency. Preserve old untagged keys and document migration.

### App caching (#103), not another framework

- Typed `get_or_set`, `@cached`, explicit key TTL, batch
  get/set if backend capability verified, scoped delete.
- Feature detection for unsupported operations and errors; async
  cancellation, async/sync overhead, testing ergonomics, borrower
  client lifetime and multi-app isolation. Do not silently retrofit
  HTTP headers or auth semantics onto non-HTTP code.
- Only add atomic add/increment primitives after Redis+InMemory
  supported semantic tests. Redis Lua/transactions require load,
  limits and shutdown behavior validation.

### Stale responses (#98), only after negative security tests

- Opt-in bounded stale-if-error and stale-while-revalidate with
  explicit max-age, no private/auth/no-store replay, no outliving
  tenant key policy. Honor request Cache-Control and Vary.
- One bounded refresh per validated key/app; cancellation and
  invalidation cannot resurrect revoked data. Strict stale headers,
  304 validation and timeout behavior. Inspect HTTP RFC 9111
  compliance where applicable; do not pretend library == shared CDN.
- Prove freshness and stampede behavior under fixed controlled load
  before marketing a latency benefit.

### Redis profiles (#102)

- Qualify standalone reconnect and library-owned timeout policy
  against redis-py version ranges first, **including default retries**.
- Independently qualify TLS identity, Sentinel, Cluster namespace
  behaviors and managed Redis; profile by profile, not a generic HA
  badge. Any distributed lease/lock needs owner tokens, leases,
  fencing and cancellation safety; consider for later 1.x.

## Milestone 1.0.0: supported core, not "every feature"

- Freeze a stable public contract (legacy and opt-in scoped APIs),
  deprecation/versioning guarantees, semantic-versioning policy and
  independently verified migration rollback.
- Publish a maintainership plan and **realistically sustainable**
  supported-Python/Redis policy; decide whether 3.8–3.10 remain
  functional-legacy or need a separately announced support change.
- Security policy for untrusted cache data, credentials, tenant keys,
  deployment across workers; real-service Redis, app-lifespan and
  failure/cancellation negative tests.
- Document capability/support matrix for InMemory/Redis vs
  *experimental* Memcached/DynamoDB, dropping unsupported providers
  only after separately approved policy.
- Accessibility of docs and usable examples for Redis/InMemory,
  migration tests for independent consumers, precise API docs,
  observability examples and incident troubleshooting.
- Reproducible measurements **on identical installed artifacts and
  independent fixed hardware** before any cross-product speed claim.
  Report throughput, p50/p95/p99/error CPU/RSS, raw samples,
  version/CPU provenance, run-to-run confidence and regressions.
- Do not promise multi-year LTS absent a maintainership budget or
  count of independent consumer integrations not actually achieved.

Feature completeness is **relative to the chosen documented API**,
not 1:1 parity with all Redis/cashews/CacheX commands.

## Executable priority and quality scorecard

| Work | User value / effort | Primary hazard | Definition of done |
|---|---|---|---|
| #99 app context | High / High | Tenant cross-app data leak | Two-app concurrent negative security tests, migration untouched |
| #96 local single-flight | High / High | Deadlock/waiter leak/private coalescing | bounded stress, creator/waiter cancellation, auth/Vary isolation |
| #50 optional events | Medium / Medium | PII leak, callback crash | private event schema, callback isolation, overhead measured |
| #97 tags | High / High | TTL/index leak or revoked data replay | invalidate/expiry/concurrency/backends with real Redis |
| #103 application cache | High / Medium-High | Hidden duplicated global state, typed serialization | minimal opt-in API, tests for owner/lifespan, benchmark |
| #98 stale | Medium-High / Very High | Private stale replay, resurrection after invalidation | RFC/auth/ETag, refresh races and cancellation tested |
| #102 HA profiles | Situational / Very High | False failover guarantees | each topology independently proven |
| #49 safe excluded params | Medium / Medium | Identity dropped from key | opt-in allowlist, auth/tenant negative tests |
| #51 Python 3.14 | High / Medium | Unsupported dependency/profile | installed wheel/sdist matrix, security and runtime |
| #55 FIPS | Medium / Medium | Silent key hash migration | unchanged golden digests, restricted-mode smoke |

**Capacity rule:** One significant core public-API feature PR at a time,
with a follow-up integration/consumer PR. Maintain normal patch releases
without blocking on future feature research. New feature lists are not
release obligations.

## Reproducible bibliography (primary sources)

- [FastAPI-CacheX PyPI 0.7.3 (Nov 23, 2026)](https://pypi.org/project/fastapi-cachex/0.7.3/);
  [HTTP feature semantics](https://fastapi-cachex.readthedocs.io/en/stable/HTTP_CACHING/);
  [application values](https://fastapi-cachex.readthedocs.io/en/stable/APP_CACHE/);
  [backends](https://fastapi-cachex.readthedocs.io/en/stable/BACKENDS/);
  [changelog](https://fastapi-cachex.readthedocs.io/en/stable/changelog/).
- [cashews PyPI](https://pypi.org/project/cashews/), version 7.6.0
  reported September 2026, feature examples with early refresh/tags/locks.
- [aiocache PyPI](https://pypi.org/project/aiocache/), 0.12.3
  released 2024-09-25; [plugin docs](https://aiocache.aio-libs.org/en/stable/plugins.html).
- [official fastapi-redis-sdk docs](https://redis.github.io/fastapi-redis-sdk/);
  [Redis caching API](https://redis.github.io/fastapi-redis-sdk/latest/guide/caching/);
  [Redis announcement Sep 24, 2026](https://redis.io/blog/the-official-fastapi-redis-sdk-is-now-available/).
- [HTTP caching RFC 9111](https://www.rfc-editor.org/rfc/rfc9111).

Revalidate exact versions and behaviors for future design PRs;
no unchecked competitor feature claim should become public marketing.

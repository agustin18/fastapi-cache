# RFC: explicit app context without breaking global FastAPICache

**Status: design proposal, not shipped. 2026-11-23 scope decision:
defer any new public per-app configuration API out of 0.7; preserve the
process-global singleton and its documented isolation limitations.
No design is accepted for implementation yet.**
Tracks [#99](https://github.com/agustin18/fastapi-cache/issues/99)
with dependencies on [#103](https://github.com/agustin18/fastapi-cache/issues/103),
[#112](https://github.com/agustin18/fastapi-cache/issues/112),
[#96](https://github.com/agustin18/fastapi-cache/issues/96) and
[#50](https://github.com/agustin18/fastapi-cache/issues/50).

## Observed legacy risk

`FastAPICache` currently holds one process-global backend, prefix,
coder, key builder, authentication policy, enabled flag and lifetime.
`FastAPICache.init(force=True)` replaces that state; `reset()` clears it.
Two FastAPI apps sharing a Python process do **not** automatically get
independent state, even if they instantiate distinct InMemory backends.
An app that resets the singleton can disrupt another app's requests.
Application code must still explicitly account for user/tenant and
middleware/permission context in every cache key.

## Candidate approaches (choose one, with proof)

| Design | Benefit | Unresolved failure mode |
|---|---|---|
| Keep only singleton for 0.7.x | Preserves every legacy behavior | Cannot honestly promise concurrent multi-app safety |
| Explicit immutable per-app config handle, bound through FastAPI lifespan/request | Clear ownership and scope; existing singleton remains opt-in compatibility path | Need routing through decorator, background tasks and concurrent workers |
| ContextVar carrying selected config | Convenient implicit selection for async requests | Inherited/stale context in tasks, spawn/teardown, threadpool and nested apps |
| Implicit discovery of `request.app` | Avoids explicit propagation for HTTP calls | Absent Request for pure functions, ambiguity during composition and tests |

**Preferred research direction, not an approved API:** explicit per-app
configuration handle with **deterministic Request-bound lookup** for HTTP
and **explicit handle passing** for non-HTTP work. Never silently fall
back to a different app's singleton when scope is ambiguous. Do not add
a new second global policy; existing `FastAPICache` behavior must remain
unchanged for one-app code unless consumers opt into the new system.
No auth/tenant identity is inferred from `request.app` alone.

## Lifecycle, privacy and compatibility invariants

- A config belongs to one declared app/lifespan; application-owned
  Redis clients are **borrowed**, not silently closed by a decorator.
  Document start/stop ownership, in-flight requests and idempotent close.
- Two apps with different prefixes, key builders, auth policies and
  backing clients must not share cached responses across concurrency,
  reinitialization, app teardown or startup order.
- Fail explicitly when an explicit app handle is missing, ambiguous or
  disposed; do not read another app's global backend as a fallback.
- Preserve ordinary `fastapi_cache` imports, legacy default key hashes,
  `@cache(...)` and singleton initialization. New handles are opt-in.
- Contextvars/thread-local methods require tests for task inheritance,
  Python threadpool, concurrent event loops, nested/mounted apps,
  explicit background work and shutdown races before acceptance.
- Cross-tenant authorization remains **application responsibility**:
  distinct app config alone cannot isolate hidden user/permission data.

## Deterministic proof required before implementation GO

1. Two concurrent ASGITransport FastAPI apps (A/B), each with distinct
   prefix, store, auth policy and key builder; reproduce current global
   conflict, then prove opt-in proposed isolation with identical URLs.
2. Request mix A-B-A-B under concurrency, Cookie/Authorization headers,
   owner/tenant distinctions, forced app restarts and reset/force interplay.
3. App A teardown while B requests are running; borrowed Redis client
   remains owned by B or the caller; no use-after-close or stale context.
4. Non-HTTP `@cache` and background tasks with **explicit** app config;
   no accidental data mix when there is no Request.
5. Reproduce no behavior change in all existing singleton keys,
   common HTTP HIT/MISS/ETag/304, Vary and Redis migration tests.
6. Installed wheel/sdist E2E, negative key/identity tests, no raw keys in
   logs, and a reproducible default-OFF/opt-in-ON overhead benchmark.

**Open decision:** whether safe app-scoping is feasible in 0.7.x or
deferred to 0.8+ / next major. No commitment to implement until the
owner approves a coherent scope and an independent reviewer verifies it.

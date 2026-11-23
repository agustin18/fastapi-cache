# RFC: caching plain functions and application values

**Status: investigation, not a promised 0.7.0 API.**
Tracks [#103](https://github.com/agustin18/fastapi-cache/issues/103)
and depends on app-context [#99](https://github.com/agustin18/fastapi-cache/issues/99)
and error policy [#112](https://github.com/agustin18/fastapi-cache/issues/112).

## Existing functionality to inventory before designing anything

The library already offers a `@cache` decorator and backend
`get/set/get_with_ttl/clear` methods. When a decorated function has no
Starlette Request, HTTP authentication bypass, Vary/ETag and
Cache-Control have no valid request context. Explicit key construction,
cache identity, user/tenant authorization, serializer and backend
client lifecycle are the caller's responsibility. Do **not** invent
a new general application cache API from a need to cache a simple
async method; test whether current functions suffice.

## Candidate shape (not a decided implementation)

- Keep existing `fastapi_cache` import paths and ordinary key identity
  for current `@cache` uses.
- Evaluate an **explicit config handle** (from #99) for non-HTTP
  synchronous and asynchronous functions, scheduled jobs and background
  tasks, without relying on a hidden singleton or Request.
- A minimal typed value/key interface may be justified only if current
  backend operations or decorators cannot supply proven use cases.
- Keep opt-in serializers explicit. Do not treat PickleCoder data as
  safe on attacker-controlled stores; preserve Python 3.8–3.13
  compatibility boundaries.
- Eviction, TTL, invalidation, error/cancellation policy and metrics
  should come from the chosen backend and accepted #111/#112 contracts,
  not an independent second cache engine.

## Required examples and negative tests

| Scenario | Acceptance question |
|---|---|
| Anonymous pure async lookup | Are args/namespace stable, deterministic and response independent? |
| Identity-sensitive lookup | Where does tenant/role/permission enter the explicit key? |
| Background task without Request | Can caller supply the app config without inheriting stale context? |
| Cached sync function | Are threadpool and cancellation semantics documented and tested? |
| Typed JSON result | Does typed decode preserve compatibility or raise predictably? |
| Backend outage, corrupt data and invalidation race | Do approved #112 error and #111 TTL/clear contracts apply? |
| Two apps sharing interpreter | Is state isolated from the other app under concurrent calls and teardown? |

Before accepting a new API: runnable examples from **installed** wheels,
an independent privacy/code review, legacy migration tests and measured
default-path overhead. If existing interfaces already satisfy the
demonstrated needs, prefer documentation over new surface area.
Do not interpret the open issue as a mandatory 0.7.0 feature.

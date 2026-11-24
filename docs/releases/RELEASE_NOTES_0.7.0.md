# fastapi-cache-stable 0.7.0 — release notes

**Published:** 2026-11-24 on PyPI. Install the exact released artifact with
`python -m pip install "fastapi-cache-stable==0.7.0"`.

## User-visible changes versus 0.6.0

- **Fix:** InMemory TTL now expires **at** the integer-second deadline
  (inclusive), consistently for bounded and unbounded caches. Zero and
  negative TTLs do not serve a stale entry. Wall-clock rollback can still
  increase remaining TTL for a still-live entry.
- **Fix:** A matching conditional `If-None-Match` must not cause an
  HTTP 304 before decoding the cached bytes. Malformed JSON/UTF-8/typed
  entries fail closed; the library does not automatically invalidate,
  unpickle untrusted data, or silently retry the handler.
- **Contract:** Standalone Redis `get_with_ttl()` returns the declared
  `tuple[int, bytes | None]` instead of the raw redis-py pipeline list;
  consumers relying on the undocumented list identity may need a change.
  Redis TTL sentinels and EX<=0 differ from InMemory.
- **Quality:** installed-artifact Redis stop/restart regression, backend
  failure/cancellation, metadata verification, docs and HTTP socket
  benchmark tooling; these add test confidence, **not** new HA or a
  guaranteed improvement in latency.

## Explicitly not added

No single-flight, cache events, app-scoped API, non-HTTP CacheManager,
tag invalidation, stale serving, new HA/TLS/Sentinel/Cluster support,
Python 3.14 certification or auto-detection of hidden tenants.
Memcached and DynamoDB remain experimental. Default import path,
legacy key formats and intentionally conservative request privacy
behavior remain compatible except for the scoped corrections above.

## Security and support

`PickleCoder` deserialization requires fully trusted cache bytes and
store access; prefer `JsonCoder` for data whose integrity is not under
the application owner's control. Explicit Authorization/Cookie and
opt-in Vary do not guarantee tenant isolation for middleware/context
variables. The project cannot promise default redis-py retry latency
from the no-retry outage probe.

## Publication state and evidence

Exact artifact hashes, Phase B evidence, security review and registry
verification are recorded in the [release status](RELEASE_STATUS_0.7.0.md),
the [GitHub release](https://github.com/agustin18/fastapi-cache/releases/tag/v0.7.0)
and [#126](https://github.com/agustin18/fastapi-cache/issues/126).

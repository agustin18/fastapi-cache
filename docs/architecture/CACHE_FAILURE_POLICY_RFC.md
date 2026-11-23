# Cache failure policy RFC — safe boundaries for 0.7.x

**Status: proposed design, not an accepted general recovery policy.**
Tracked in [#112](https://github.com/agustin18/fastapi-cache/issues/112)
with dependencies on [#99](https://github.com/agustin18/fastapi-cache/issues/99)
and [#103](https://github.com/agustin18/fastapi-cache/issues/103).
No changes to the published 0.6.0 artifact.

## Characterization of published 0.6.0

| Failure | Observed behavior | Pending decision |
|---|---|---|
| Backend read exception | Log exception type; recompute endpoint | Narrow error classification |
| Backend write exception | Log, return computed response with MISS/ETag | Persisted vs non-persisted response metadata |
| Coder cannot encode | Return response uncached | Header/status contract |
| Coder encode error | Propagate | Potentially narrow safe fallback |
| Coder decode error | Propagate (no invalidation) | Fail-closed vs opt-in recover |
| Bad cached bytes + matching If-None-Match | 0.6.0 could return 304 before attempting decode | Scoped correction in PR #124 |
| Cancellation | Normally propagates | Backends and per-version verification |
| Untrusted PickleCoder data | Unsafe deserialization | Never auto-unpickle untrusted values |

## Proposed review decisions

1. Decode and validate cached data **before** any cache-hit 304. The scoped
   correction in PR #124 retains fail-closed decode errors. No automatic
   eviction, retry or general policy flags are added.
2. Consider later explicit opt-in recovery only for recognized invalid data
   formats and one recomputation; do not catch application logic errors or
   suppress task cancellation. No infinite invalidation/recompute loop.
3. Treat backend read, backend write, coder encode and coder decode failures
   as different classes. Current broad backend-read fallback is provisional.
4. Define honest MISS/ETag/Cache-Control semantics after a failed write:
   response-byte ETag is not proof the backend actually stored the value.
5. Never auto-unpickle attacker-modifiable bytes; keep raw keys, credentials,
   auth headers and payloads out of logs and high-cardinality event labels.
6. Configure future policies explicitly per application (#99), not via a
   new hidden process-global setting. Plain function caching (#103) must not
   inherit HTTP-only 304 rules.

## Mandatory tests before any broader fallback

Invalid JSON, invalid UTF-8, incompatible typed models, conditional 304
with malformed bytes, backend read/write timeout or disconnect, cancellation,
failed invalidation, simultaneous corrupt reads, user/tenant isolation,
Redis loopback E2E, and log redaction. Pickle trust must be reviewed separately.

**#112 remains open** until an approved matrix and tested implementation or
an explicit documented rejection exist. No 0.7 release authorization.

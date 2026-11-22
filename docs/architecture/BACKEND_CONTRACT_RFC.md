# Backend contract RFC — testable scope before widening support

**Status: proposed contract, not a change to shipped 0.6.0 behavior.**
Tracked under [#111](https://github.com/agustin18/fastapi-cache/issues/111).
The reusable `tests/test_backend_contract.py` test verifies a conservative
shared subset on InMemory and a **loopback, test-only** standalone Redis server.
It does not promote experimental providers to supported status.

## Shared contract and capability table

| Operation | InMemory | Redis standalone | Memcached | DynamoDB |
|---|---|---|---|---|
| get/set bytes | Supported | Supported | Experimental | Experimental |
| No-expiry TTL | -1 | -1 | Fixed artificial 3600 | -1 |
| Missing TTL | 0 | -2 from Redis | Fixed artificial 3600 | 0 |
| Finite TTL | Local seconds | Redis TTL seconds | Not real remaining TTL | Checked by get_with_ttl |
| `get()` after expiry | Local check | Redis expiry | Client-owned | **Known gap:** may return expired item |
| `clear(key=)` | Supported, scoped | Supported, scoped | NotImplemented | NotImplemented |
| `clear(namespace=)` | Scoped prefix | Scoped SCAN/UNLINK | NotImplemented | NotImplemented |
| Backend client close | No external client | Caller owns Redis client | Caller owns client | **Known gap:** close lifecycle |
| Redis Cluster namespace clear | N/A | Explicitly unsupported | N/A | N/A |

`get_with_ttl()` has the declared `Tuple[int, Optional[bytes]]` return shape
on supported Redis and InMemory backends. Redis pipeline `execute()` returns
a list, so the Redis adapter explicitly returns a tuple without changing the
TTL sentinel or data bytes. This corrects the source API contract and should
be assessed by any downstream application that relied on the previous
undocumented list identity; published 0.6.0 bytes remain unchanged.

A `get_with_ttl` miss has **no bytes** and nonpositive TTL. The underlying
Redis `TTL` command returns -2; InMemory returns 0. A universal exact
sentinel is not yet guaranteed across providers. This RFC must be reviewed
before making that a breaking public assertion.

Cache keys, values and namespaces in tests are synthetic. All Redis writes
are under a per-test random namespace with selective cleanup only;
**no FLUSHDB/FLUSHALL**, remote Redis, credentials or production data.
A real Redis 7.4 profile is required before claiming standalone parity.

## Pending decisions and hardening

1. [#112](https://github.com/agustin18/fastapi-cache/issues/112): define corrupt
   bytes and coder/backend failures; distinguish fail-open recomputation,
   fail-closed exceptions, observability and cancellation semantics.
2. [#45](https://github.com/agustin18/fastapi-cache/issues/45):
   reproduce and fix DynamoDB expired `get()` inconsistency and client
   close, with an emulator/real-service qualification before changing
   advertised support. Memcached fixed TTL and unsupported clear require
   a truthful capability decision; never fake remaining TTL.
3. [#102](https://github.com/agustin18/fastapi-cache/issues/102):
   timeout, reconnect, pool lifecycle and teardown with a real service;
   TLS/Sentinel/Cluster/HA is a later, separately qualified track.
4. Record operation-specific capability flags or explicit exceptions before
   exposing a public API that assumes equivalent backends.
5. Verify expiry boundaries (TTL=0, negative TTL, strict clock comparisons),
   concurrency, invalidation races and cancellation independently. Passing
   the simple shared smoke test does not complete those requirements.

The existing distributed package and external client ownership remain
unchanged. Future implementation should add contract variants and
explicit exceptions without silently changing legacy key digests.

# C2 / D4 backend contract — published in 0.8.0

Status: accepted C2 implementation merged as
`2aa9a031a5ad6c1a92759314d5e9d6172cb224e6` on accepted RFC #147 and merged
C1 #148; published in 0.8.0. Scope: #111 supported built-in
contracts only. No API or
behavior changes to legacy Backend, TTL values, cache keys, coder or retry
policy. C3 (#112) owns decorator failure/serialization policy.

## Capability descriptor

Internal `fastapi_cache._backend_contract.backend_capabilities(backend)`
returns a frozen `BackendCapabilities` snapshot. Status values are
supported, experimental, unsupported, unknown; they describe the adapter,
not a probe or guarantee of a deployed service. Exact built-in classes only;
no subclass inheritance, declaration-based promotion, plugin registry,
mandatory extra imports or I/O. Unknown/custom backends keep legacy ABC
compatibility and are not eligible for app scope. C1 now uses this single
descriptor for the same admission rule; no expansion. Redis flags reflect
the adapter's existing cluster classification, not HA/topology discovery.
Use bytes-returning Redis clients (decode_responses=False); unsupported
client configurations are not certified by this descriptor. Configuration
and client internals must not be mutated while in use.

| Capability | InMemory | Standalone Redis | Redis Cluster | Memcached | DynamoDB | Custom |
| --- | --- | --- | --- | --- | --- | --- |
| get/set bytes | supported | supported | experimental | experimental | experimental | unknown |
| truthful remaining TTL | supported | supported | experimental | unsupported (fixed 3600) | experimental | unknown |
| clear exact | supported | supported | experimental | unsupported | unsupported | unknown |
| clear namespace | supported | supported | unsupported | unsupported | unsupported | unknown |
| app scope | supported | supported | unsupported | unsupported | unsupported | unsupported |
| atomic compare-delete | unsupported | unsupported | unsupported | unsupported | unsupported | unknown |
| ownership | local | borrowed | borrowed | borrowed | experimental | unknown |

Supported means candidate contract within qualified profiles, not that a
particular CI run has passed. Experimental does not mean supported. No new
public capability API, abstract methods, ownership transfer, close callback
or automatic backend error wrapper. Caller owns the borrowed Redis/Memcached
client; C1 handles drain but never close them. DynamoDB has adapter-managed
initialization and unresolved close behavior (#45); no lifecycle parity claim.

## Operation semantics

- Backend.get returns bytes or None; get_with_ttl returns a tuple
  (integer seconds, bytes or None). InMemory misses (0,None), Redis
  misses (-2,None), both persistent (-1,bytes). Empty bytes are data.
  A Redis TTL of 0 may accompany a still-live value (server rounding).
  Memcached's constant 3600 even on miss is not a remaining TTL.
- set replaces payload and expiry; expire=None persists, including when
  replacing a finite entry. InMemory uses integer wall-clock inclusive
  deadline, nonpositive TTL is immediate miss at the observed clock;
  backward shifts can extend a still-live entry, never revive a removed
  entry. Redis EX <= 0 raises; do not normalize across providers. Redis
  server time/rounding governs expiry. No cross-clock or elapsed-time SLA.
- Legacy clear keeps nonempty namespace precedence over key, empty
  namespace allows exact key, no arguments are no-op for supported stores.
  Literal namespace matches namespace + ":"; Redis escapes glob
  metacharacters and filters scan results. Return actually removed count
  (InMemory physically removed entries, including unobserved expired
  entries; Redis UNLINK/DELETE result). Redis SCAN is non-atomic, can
  repeat keys and concurrent writes may survive; counts are not a
  snapshot of unique logical entries under concurrency. No flush.
  C1 handle.clear rejects ambiguous or foreign exact keys before I/O.
- Backend calls propagate cancellation and original exceptions; direct
  callers must treat exception text as potentially sensitive. No new
  logging, no generic wrapping/classification or library-level retry.
  Unknown write/clear outcome may be committed or partial; do not retry
  automatically. Redis client retry/timeout policy is caller-controlled;
  existing daemon stop/restart evidence is retry-disabled only. InMemory
  cancellation while waiting for its lock performs no mutation; once
  acquired local operations are synchronous. C1 close/drain behavior
  unchanged. No linearizable multi-operation guarantee or atomic repair.

## Evidence and residual scope

New workflow installs candidate wheel AND sdist in independent venvs,
outside source checkout, on standard Python 3.8–3.14 with real disposable
Redis 7.4. Tests use random prefixes and selective cleanup, never flush.
Runs shared contract, bounded/unbounded clock boundary, literal clear,
partial Redis clear/cancellation, uncertain write, client ownership and
C1 lifecycle regression. Exact job logs identify SHA, artifact digests and
PASS/FAIL; before execution all are NOT RUN. Tests of fault injection
around real Redis calls are not network-fault/HA certification.

Experimental Memcached and DynamoDB installed-adapter characterization
uses synthetic clients on Python 3.12 (fixed TTL, expired direct read,
unsupported clear and close gap). Real Memcached/DynamoDB/emulator,
Redis Cluster, Sentinel, TLS, failover and all-provider parity remain
NOT RUN, outside C2. #45 and #102 remain separate; keep broad #111 open
until residual scope is independently dispositioned. #112 owns policy
changes; #53/#100 final privacy/performance and release gates remain.

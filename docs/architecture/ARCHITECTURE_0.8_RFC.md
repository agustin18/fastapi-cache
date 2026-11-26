# RFC: 0.8.0 architecture foundations — application scope, backend and failure contracts

**Status: ACCEPTED design record for scoped implementation, not a release approval.**
Baseline: published 0.7.2, tag source `8cb3f4fe82e3d02cb6ae7874c03d82f94d9df822`;
planning snapshot `ad2f7038cf936b6b8d975d568f698c04de7277b1` (post-#146).
Revised HEAD `dee1b5e6d049f6ed8d3a8be79760841a81b24feb` independently audited and merged as `14ad64b002aa17aa28db7325be76831de10e524f`; maintainer requested C1. Each implementation PR still requires review.
No code, distribution metadata or publication changes in this RFC.

Tracks [#99](https://github.com/agustin18/fastapi-cache/issues/99),
[#111](https://github.com/agustin18/fastapi-cache/issues/111) and
[#112](https://github.com/agustin18/fastapi-cache/issues/112).
Consolidates [app context](APP_CONTEXT_RFC.md), [backend contract](BACKEND_CONTRACT_RFC.md)
and [cache failure policy](CACHE_FAILURE_POLICY_RFC.md) as the proposed common
decision record; those documents remain historical research, not independently
approved implementation specifications. [#53](https://github.com/agustin18/fastapi-cache/issues/53)
and [#100](https://github.com/agustin18/fastapi-cache/issues/100) are cross-cutting.
The separate APPLICATION_CACHE_RFC.md (#103) is not part of this proposal.

## 1. Baseline and problem

0.7.2 expands the Python range, not runtime behavior. Source inspection of
`fastapi_cache/__init__.py`, `decorator.py`, `types.py`, `coder.py` and
`backends/` establishes the following baseline; this is not a newly executed test.

- FastAPICache stores backend, prefix, expiry, coder, builder, status header,
  enable and authenticated-cache policy in class variables. init rejects a
  second initialization unless force=True; reset clears the global state
  without closing a caller-owned client. Multiple apps in a process can
  interfere, and async work may observe different global values if reset
  or force occurs during an await. Distinct InMemory objects alone do not
  fix routing through the singleton.
- The decorator adds Request/Response injection, bypasses uncacheable
  requests, reads global defaults and builds a key, reads bytes and decodes
  before a HIT/304; on a miss it runs the endpoint and may encode/store.
  The enable check currently lives in _uncacheable, and must be included
  in any scope change, not just backend selection.
- Legacy KeyBuilder receives namespace and optional Request/Response,
  args/kwargs and may be async. Default hash, generated-route scoping and
  vary-v1 format must remain compatible. A custom builder may ignore its
  namespace argument; a prefix alone cannot enforce isolation.
- Backend ABC requires get, get_with_ttl, set and clear, not a universal
  close API or capability API. Standalone Redis wraps a caller-provided
  client; InMemory uses instance storage and a lazy async lock.
- #114/#123/#124/#131/#133 already characterize tuple shape, inclusive
  InMemory TTL, decode-before-304, failure behavior and Redis daemon
  restart with retries disabled. They do not resolve broad #111/#112.
- #53 covers unknown authorization/tenant/locale/context inputs and
  cardinality; #100 is descriptive, not a performance SLA or HA claim.

## 2. Goals and explicit non-goals

Goals: opt-in deterministic scope for HTTP cache use, immutable config
snapshots per operation, explicit resource ownership and shutdown,
truthful backend capabilities and documented failure decisions. Preserve
existing imports, singleton, decorator signature behavior, supported
interpreter ranges, keys, bytes and default HTTP contracts for legacy users.

Non-goals: automatic user/tenant isolation; global state redesign or
automatic app-state discovery for unmodified decorators; ContextVar-only
routing; new public plain-function caching API (#103); single-flight
(#96), events (#50), advanced Redis integrations (#102), tags (#97),
parameter filtering (#49), stale serving, distributed locks, backend
graduation, deprecating FastAPICache, new mandatory dependencies or
breaking default changes. Fix separately any reproducible P0/P1 defect;
do not hide it in a feature or waive it as a known limitation.

## 3. App scope: proposed API and resolution (#99)

### D1: proposed frozen C1 API

The following names/signatures are proposed for maintainer ratification,
not shipped. Public imports are additive from `fastapi_cache`:
`CacheConfig`, `CacheHandle`, `CacheScopeError` (a RuntimeError subclass).
No new dependency; use Python 3.8-compatible annotations.

- `CacheConfig(backend, *, scope_id, prefix="", expire=None, coder=JsonCoder,
  key_builder=default_key_builder, cache_status_header="X-FastAPI-Cache",
  enable=True, cache_authenticated=False)`: frozen configuration with
  explicit physical scope_id independent of the logical legacy prefix.
  Freeze references, not arbitrary mutable caller-owned backend/coder
  internals; callers must not mutate their configuration concurrently.
- `CacheHandle(config)`: borrowed-only, no ownership parameter in C1.
  `await handle.start(app)` atomically binds/activates in the running
  loop; `await handle.aclose(*, timeout=30.0)` drains/unbinds this handle.
  Reserved state attribute `_fastapi_cache_app_handle_v1`; no
  process-global registry or ContextVar routing. No user replacement of
  this reserved attribute. Reject occupied slots, including foreign objects.
- Extend `cache(..., *, scope="legacy", handle=None)` after the existing
  positional parameters. Allowed scopes: "legacy"/"app". Supplying a
  handle with default "legacy" selects explicit mode; supplying a handle
  with scope="app" is rejected at decoration time as ambiguous. Invalid
  scope or non-handle value also rejected at decoration time.
- `await handle.clear(*, namespace=None, key=None) -> int` is the only
  proposed explicit background/non-request operation in C1 (see D2).
  No new decorated plain-function API (#103).

Illustrative lifespan usage (proposal only):

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_cache import CacheConfig, CacheHandle
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

@asynccontextmanager
async def lifespan(app):
    handle = CacheHandle(CacheConfig(
        backend=InMemoryBackend(), scope_id="orders-v1"
    ))
    await handle.start(app)
    try:
        yield
    finally:
        await handle.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/orders")
@cache(scope="app")
async def orders():
    return {"items": []}
```

| Invocation | Resolution | Missing, conflicting, stopped |
| --- | --- | --- |
| Explicit handle, HTTP | Exact active handle must be bound to exact request.app in reserved slot | CacheScopeError; no other lookup |
| scope="app", HTTP | Exact request.app binding, no parent search or fallback | CacheScopeError |
| Legacy decorator, neither option | Existing FastAPICache path even if app.state has binding | Preserve legacy behavior |
| Either scoped decorator without Request | Reject, including direct calls | CacheScopeError before lookup/write |
| Existing direct decorated call without opt-in | Existing singleton behavior | Preserve legacy behavior |

Use `scope="app"` for static routers and repeatable lifespan startup;
an explicit decorator handle is valid only for its original generation.
A captured closed handle fails after restart rather than switching
generations implicitly. Mounted apps resolve exact Request.app; test
actual Starlette behavior and reject missing binding, never inherit the
parent implicitly. DI may pass handles for explicit scoped operations;
no inference from dependency values, task-local or thread-local state.
An unbound HTTP app cannot borrow another app's handle merely by sharing
a router. Scoped error messages are constant, sanitized, do not contain
IDs, prefixes, credentials or keys; never trigger legacy fallback.

Per-route overrides of coder/key builder/expiry/auth/variation follow
legacy precedence unless an opt-in difference is independently accepted.
The handle is resolved once before scope-sensitive enable/bypass checks,
then immutable config is captured and held through every await; bypass
must release a lease. Preserve existing signature injection, wraps,
sync-threadpool behavior, response model inference, default key builder
and Vary/ETag/private-response guards. Do not use global getters in the
app branch. Legacy zero-expiry truthiness behavior is not silently fixed.

### D2: exact proposed physical key and clear contract

Reserve the literal root `__fastapi_cache_app_v1__` for opt-in mode.
Scope identifiers must be strings matching ASCII fullmatch
`[a-z0-9][a-z0-9_-]{0,63}` (no normalization or trimming).
Reject empty, non-ASCII, uppercase, colon, glob, whitespace and
overlength identifiers before activation. The same logical application
uses the same scope_id across workers and restarts; a different
logical application sharing a physical store MUST use a different
scope_id. No inference from hostname, Request or Python object ID.

Define H(s) = SHA-256 of strict UTF-8 bytes of s, lowercase 64 hex
characters, with no Unicode normalization. Define:

```text
root = "__fastapi_cache_app_v1__"
scope = root + ":" + scope_id
group = scope + ":" + H(route_namespace)
physical_key = group + ":" + H(logical_key)
```

route_namespace is the decorator's exact namespace string (including
the empty string); logical_key is the complete existing key pipeline
output: invoke sync/async builder with logical `prefix:namespace`,
apply existing default generated-route scoping and vary-v1 processing,
then envelope **once**, immediately before any backend call. A
custom builder result that already looks like a physical key is still
logical input and is hashed; it cannot select a different physical
scope or cause a double-wrap at lookup versus write. Both namespace
and logical key must be strings encodable as strict UTF-8; reject
invalid values with sanitized error, no backend I/O. Empty logical key
is rejected in scoped mode (legacy unchanged). No special treatment of
colon, glob or Unicode within logical namespace/key; hashes keep them
out of physical keys. Logical namespace is a distinct field so even a
builder that ignores its namespace cannot collide across two different
route namespaces in scoped mode. Equal logical keys within the same
scope and route namespace intentionally refer to the same entry;
caller still owns all response-defining inputs. SHA-256 digest
collisions are a cryptographic assumption, not a tenant security claim.

Golden vector (ASCII input namespace "orders", logical key "raw",
scope_id "shop-a"; single physical key, shown on one line):

```text
__fastapi_cache_app_v1__:shop-a:1c168adb00d208e42f93314529f1fa9c0427eb63233ceda95a5db52b7012a719:d7439bee24773bcbfa2d0a97947ee36227b10d1022b1a55847e928965bb6bfde
```

H("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
Test composed/decomposed Unicode as distinct, invalid surrogates as
rejected, same logical key in shop-a versus shop-ab, same key with
different namespace and Vary, malicious builder returning a foreign
physical key, and deterministic cross-process generation. The ASCII
envelope has exactly four colon-separated fields (scope plus two
fixed-length digests) and length <= 219 characters.

| Scoped clear call | Exact backend operation |
| --- | --- |
| clear() | clear(namespace=scope) — entire this scope |
| clear(namespace="") | clear(namespace=group for H("")) — default route group only |
| clear(namespace="orders") | clear(namespace=group for H("orders")) — exact group only |
| clear(key=physical_key) | clear(key=physical_key) — one exact key after validation |
| Both namespace and key; malformed/foreign key | CacheScopeError, no I/O |

The exact-key API accepts only a full physical key (not a logical
builder output), validated by splitting into exactly four fields:
literal root, exact current scope_id, two lowercase 64-hex digests;
reject empty, foreign, malformed, glob or suffix input. Document how
to derive it from the formula; no key-discovery API or raw-key logs.
Namespace clear passes the prefix without trailing colon: both
InMemory and standalone Redis enforce prefix + ":"; use the existing
Redis literal glob escaping and boundary check. Return actual removal
counts; no atomic whole-scope invalidation promise, no broad flush.
In C1 restrict opted-in handles to the built-in InMemory and
standalone Redis backend types (lazy optional import; RedisCluster
excluded); third-party backends remain usable on legacy path.
Any expansion requires C2 conformance/explicit capability acceptance.

**Reservation and migration:** this is an opt-in key format only.
The legacy path is byte-for-byte unchanged and can technically write
arbitrary strings (including reserved roots) via a custom builder or
prefix. Therefore the operator MUST reserve this root across all
writers using a shared store, including legacy clients, or use a
dedicated database/store. Existing entries under the reserved root
must be audited before activation; no scan or automatic collision
detection on startup, no global or cross-process registry. Two
handles with duplicate scope_id on the same physical store are a
configuration error by contract but not automatically detectable
(across distinct client objects/processes, or legacy writers).
Do not promise prevention in that misconfiguration. A malicious
backend or direct Redis writer is outside this boundary. Separate
store is recommended if reservation cannot be enforced. Sharing a
bounded InMemory instance also shares capacity/eviction, not response
keys; distinct instances recommended for resource isolation.

Opt-in starts cold under the new reserved root; no automatic copy,
dual-read, fallback or purge of legacy entries. Rollback uses the
unchanged legacy configuration/namespace only if still valid; scoped
entries may remain until TTL or explicit scoped clear (persistent
entries require planned cleanup). Rotate scope_id for incompatible
coder/key/representation changes; same scope_id intentionally reuses
compatible scoped entries across restarts. C1 gate: golden formula,
real backend spy/Redis+InMemory negative tests, scoped clear boundaries,
legacy goldens, migration documentation, and maintainer acceptance of
cold-cache and reservation limitations.

### D3: borrowed-only lifecycle and cancellation

State machine: NEW -> ACTIVE -> DRAINING -> CLOSED. One handle per
app/lifespan and running event loop; restart creates a fresh handle.
`start(app)` requires NEW, running loop, valid config and vacant
reserved slot; bind and transition synchronously without await
between validation and installation. Failed validation leaves NEW,
no binding or resource close. Reject repeated start, wrong loop or
foreign app. Independent handles/workers own independent bookkeeping;
no cross-loop thread safety for InMemory locks or Redis clients.

Borrowed-only in C1: never close, disconnect, reset, flush or dispose
caller-owned resources, including failures/cancellation. Owned mode,
factories, cleanup callbacks and automatic closing are explicitly
DEFERRED beyond 0.8; no abstract close added to Backend. Capture
immutable config and acquire a lease on the running loop before any
scoped operation/bypass, including explicit clear. State check and
counter increment are synchronous on that loop; release in finally
on success, exception and cancellation. Hold lease through all
awaited endpoint, builder, decode/store and threadpool work; no use
of borrowed resources by cache after release. Test sync work
cancellation (thread may outlive await; never promise its termination).

`aclose(timeout=30.0)` accepts a finite positive seconds budget
(Python 3.8-compatible wait primitive); invalid value rejects before
state mutation. NEW close transitions CLOSED without binding; ACTIVE
close transitions DRAINING synchronously, prevents new leases, retains
identity-bound state until drained. If already DRAINING, join the
same drain signal with caller-specific deadline, do not cancel admitted
requests. When lease count reaches zero, finalize CLOSED and remove
the slot only if it still contains this exact handle, synchronously.
No background task required. If deadline expires or closing task is
cancelled, propagate TimeoutError / CancelledError, stay DRAINING
until final lease release completes finalization, never close the
client or allow a new handle before drain; repeated close can wait
again. Concurrent closers share drain/finalization but can have
different wait outcomes. CLOSED close on owning loop is idempotent.
Reject wrong loop. If reserved slot was tampered with, do not remove
foreign state; report sanitized configuration error at validation
rather than allowing fallback. Scope owner must wait for successful
drain before releasing borrowed resources; timeout is not permission
to close them. Application shutdown policy if a caller never drains
is explicitly outside library ownership, document this limitation.
No retry, hidden global flag, automatic cancellation of other tasks
or single-flight. Test cancellation at every lease boundary,
close during active request, timeout then drain, repeated concurrent
close, failed startup, restart and no client close calls.

## 4. Backend contract (#111)

Keep Backend ABC signatures and custom implementations source compatible.
Use an internal/optional capability descriptor (shape ratified before C2), not new abstract
methods or blanket protocol parity. Capability can be supported,
experimental or unsupported; unknown custom backends must not be assumed
to have atomic compare-delete, cluster clear or ownership support.

| Operation | InMemory | Standalone Redis | Memcached | DynamoDB |
| --- | --- | --- | --- | --- |
| get/set bytes, including empty | Supported | Supported | Experimental | Experimental |
| get_with_ttl result | tuple; miss (0,None) | tuple; miss (-2,None) | artificial 3600, not qualified | experimental; miss 0 |
| persistent TTL | -1 | -1 | not truthful remaining TTL | -1, experimental |
| expire <= 0 | immediate miss | EX <= 0 rejected | not qualified | not qualified |
| exact expiry | integer wall-clock inclusive | server TTL; rounding differs | not qualified | get expiry gap |
| clear exact / literal namespace | scoped / scoped | scoped / SCAN+UNLINK | unsupported | unsupported |
| client ownership | instance-local; no external client | caller-owned by default | caller-owned, experimental | close gap |
| compare-and-delete | not currently promised | not currently promised | unknown | unknown |

Redis Cluster namespace clear remains explicitly unsupported. No
TLS/Sentinel/HA certification. Preserve the existing public sentinel
and TTL divergence; a returned payload (including b"") is not a miss
solely because TTL == 0, as Redis may still have a live subsecond entry.
No expired value after a documented expiration observation, no claim
of cross-clock monotonicity. Existing InMemory wall-clock rollback can
increase remaining TTL for a still-live item; deleted entries cannot
revive. Specify overwrite, no-expiry and expiry rounding per provider.
Test exact time boundaries using fake clock and Redis TTL/PTTL envelopes,
not flaky sleeps alone.

Propose new scoped clear API reject ambiguous key+namespace, empty or
out-of-scope key and unsupported capability before I/O; preserve
legacy precedence/no-op behavior. Return actually removed counts, not
enumerated candidates; namespace scan is non-atomic, concurrent writes
may survive, cancellation may leave partial progress. Do not retry a
partially completed clear or claim linearizable invalidation. No flush.
Set/get/clear exceptions do not imply operation did not happen
(timeout can follow a committed write); no blanket retry. No stale
resurrection guarantee across arbitrary concurrent user writes. Distinguish
custom backend programmer error from transport failure; adapter-specific
mapping requires an approved bounded list and no new mandatory exception
base for third-party classes. Cancellation propagates and ownership is
independent from operation success. Keep experimental issues #45 and
real-service qualification separate; use PASS/FAIL/NOT RUN by capability.

## 5. Failure and serialization policy (#112)

Preserve legacy exactly unless a separately reviewed correctness fix is
needed. New app policy defaults to equivalent behavior, not silent
recovery. Prefer a small immutable per-handle policy, opt-in independently
of choosing app scope. Distinguish these cases (proposed):

| Event | 0.7.2 behavior | New opt-in policy proposal |
| --- | --- | --- |
| Backend GET exception | log type, recompute | default same; optional strict propagation only for classified backend errors |
| Backend SET exception | return computed response; MISS, representation ETag, possible 304 | default same; optional truthful storage-failure status and conservative HTTP handling, exact headers to approve |
| can_encode false | bypass storage | unchanged |
| can_encode/encode exception | propagate | unchanged; no masking endpoint/coder bugs |
| Known corrupt JSON/UTF-8 or invalid typed entry | decode error propagates; no 304 first | optional one recompute for vetted built-in coder errors |
| Unknown/custom coder exception | propagate | propagate unless explicitly qualified |
| Endpoint/key-builder exception | propagate | unchanged |
| Cancellation | propagates | unchanged |
| Clear/cleanup error | operation-specific error | propagate/report sanitized class; no repeated deletion |

Opt-in recovery candidate: only for narrowly recognized JsonCoder /
TypedJsonCoder format failures (review UnicodeDecodeError, JSONDecodeError,
Pydantic validation and tagged-object conversions individually; never
catch all TypeError/ValueError). Exact built-in coder trust boundary;
no automatic pickle recovery, no extra unpickle, no arbitrary custom
coder classification. Pickle is unsafe on attacker-modifiable bytes;
ETag is not authentication. No weakening of decode-before-304.

Prefer recompute once without deleting or overwriting the suspect entry
unless a backend provides reviewed atomic compare-and-replace/delete
against the exact observed version. An unconditional clear(key) or SET
can destroy a fresh concurrent write; do not introduce either as
corruption recovery. A read followed by ordinary clear/set is not atomic.
Minimal safe option for 0.8: recompute and return uncached for that
request (may recur on a later request; operators rotate namespace or
remove bad entry safely). No internal retry, no promise of one global
recomputation and no automatic cleanup if compare primitive unavailable.
Consider deferring broader repair beyond 0.8. For successful recomputation
on corruption, propose no cache-driven 304, no stale ETag/status,
conservative no-store while preserving stricter endpoint directives;
specify returned vs injected Response and Vary behavior explicitly.
A failed endpoint or cancellation propagates; no cached stale fallback.
A failed backend write can still yield a valid representation validator,
but never a claim of stored bytes. Proposed opt-in failed-store response:
omit library-generated ETag/304 and public freshness, conservative
no-store, MISS or an explicitly approved separate status (not events).
Do not strip application-owned headers blindly. Maintain authentication
private/no-store, no bypass of explicit Request/key-builder rules.
Review precise header/status behavior in all branches before coding.

Backend timeouts: caller owns Redis retry/socket policy today. Do not
promise bounded latency with default redis-py retries. Prefer no new
generic timeout wrapper until cancellation/unknown commit behavior is
reviewed; if approved later use Python 3.8-compatible primitives and an
explicit budget, distinguish deadline from caller cancellation. No
retry on unknown write or clear outcomes.

Logging: use fixed operation/error category and sanitized exception
class (or bounded allowlist); never raw keys, namespace values that
contain identity, exception text, payload, headers, credentials,
connection URLs or unbounded metric labels. Existing legacy namespace
logging should be characterized; any verified disclosure gets separate
security triage. No new callback/event API (#50).

## 6. Privacy and security (#53)

App isolation is configuration/storage separation, not authorization.
Applications must include every response-defining principal, tenant,
permission/version, locale and hidden dependency/context in a stable
identity-aware builder, or bypass caching. Never automatically exclude
current_user; do not trust forwarded headers as identity. Preserve
Authorization/Cookie default bypass, explicit Request bypass with default
builder, authenticated opt-in requiring a custom builder, private/no-store
for auth opt-in and returned Response Vary guards. Reject ambiguous scope
before backend access, and ensure no fallback to singleton on missing
binding, wrong app, closed handle or wrong loop. Test deliberate custom
builder collisions across apps, same URL/function/router, shared Redis,
prefix glob metacharacters, namespace collisions and foreign explicit keys.
Tenant-sensitive response on same app with incomplete key is an
application-owned risk, not something app scope certifies. Use synthetic
principals only; no real credentials, no remote Redis or destructive flush.

## 7. Compatibility and migration

Default path keeps import `fastapi_cache`, FastAPICache.init/reset/clear,
legacy decorator args and behavior, Python >=3.8,<3.15, Redis range,
key goldens (including generated route and vary-v1), ETag and coder bytes.
No forced init migration or deprecation; no new optional package promoted.
New scoped keys use the D2 versioned physical namespace after ratification:
cold cache on opt-in, do not read unrelated legacy keys, rollback disables
opt-in and reuses old namespace only if still valid; never reinterpret
scoped entries as legacy. Migrating an app with existing Redis keys is a
documented operator choice, not automatic copy or deletion. Preserve
third-party Backend/KeyBuilder/Coder shape and positional signatures.
A change to any legacy default requires separate acceptance, impact
analysis and regression tests; if necessary, defer to a future major.

## 8. Evidence plan and acceptance matrix

The RFC is design-only; **all new implementation evidence below is NOT
RUN**. CI green for this doc is not proof of the proposed runtime.

| Gate | Concrete evidence |
| --- | --- |
| Baseline | Reproduce singleton interference on installed 0.7.2 with two concurrent ASGI apps, differing config; retain negative test |
| C1 resolution | explicit/app/legacy table, absent/conflict/wrong loop, no Request, mounted apps/shared router, force/reset during awaits, sync + async, startup order, restart, teardown during request, borrowed resource counters, drain/timeout and cancellation (owned deferred) |
| C2 contract | installed wheel/sdist reusable InMemory + standalone real Redis 7.4 conformance; bytes, tuple, sentinel/zero TTL, overwrite, literal scoped clear/count, partial cancellation, expiry/rollback; experimental providers explicit PASS/FAIL/NOT RUN |
| C3 policy | malformed JSON/UTF-8/typed/unknown coder, trusted Pickle boundary, matching If-None-Match, failed get/set, encode failure, failed invalidation if ever proposed, simultaneous readers/writers, timeout/cancel, no retry or leaked sensitive logging; returned/injected response and privacy header cases |
| C4 isolation | two apps sharing physical Redis with distinct scope, same route and hostile builder, disjoint clears; two identities per app, hidden-context negative example, multiworker and separate event-loop cases, legacy goldens |
| Performance | preregister scenarios, run baseline 0.7.2 and candidate on same hardware/interpreter/service, interleaved repeats; default OFF and ON, hit/miss/bypass, concurrent lifecycle and memory; report samples/median/tails/variance and limitations, no speedup or SLA claim |
| Compatibility | functional standard CPython 3.8–3.14 incl Pydantic profiles and supported Redis client lanes; security 3.11–3.14; no 3.14t/3.15 claim |
| Release | actual built wheel/sdist installed from exact SHA outside checkout; 25-job Phase B minimum (1 build, 14 migration/rollback, 10 security), existing jobs unchanged; new opt-in migration/rollback and negative tests additive, exact verifier updated only if matrix expands |

Use deterministic barriers/events and bounded watchdogs for races rather
than timing-based assertions alone. Fake clock tests do not certify
Redis service behavior. Real Redis fault tests distinguish single-attempt
retry-disabled evidence from default retry behavior. All test resources
scoped, isolated and cleaned up; no FLUSHDB/FLUSHALL. Report NOT RUN
honestly; no unsupported capability claim. A reproducible package-owned
P0/P1 privacy/security or compatibility defect blocks promotion.
Performance thresholds to preregister with reviewer before using them
as gates; no invented universal percentage on noisy hosted CI.

## 9. Alternatives and tradeoffs

| Approach | Advantage | Reason not preferred alone |
| --- | --- | --- |
| Keep global singleton only | Zero API change | Does not isolate apps |
| ContextVar | Convenient propagation | Stale/inherited tasks, thread/loop ambiguity; not a sole source |
| Implicit app.state for all decorators | Easy setup | Changes existing behavior, mounted apps and missing state ambiguous |
| DI-only provider | Explicit FastAPI integration | Direct calls and signatures awkward; can complement handle |
| New per-app decorator class only | Clear ownership | Router reuse and migration friction; could be future adapter |
| Explicit handle + explicitly opted-in request.app lookup | Deterministic, legacy preserved | Extra lifecycle, scope-envelope, validation and performance cost |

Recommend last option subject to decision table and evidence. Reject
silent global fallback for new mode. If physical scope, lifecycle or
compatibility cannot be made defensible, narrow the borrowed-only
proposal further or defer rather than ship an unsafe API.

## 10. Decision register — independent review and revised proposal

Independent auditor feedback supplied by the maintainer on 2026-11-26
reviewed RFC HEAD `dc9a8f337e05e20ecda63a164811d390eb4338ea`.
It accepted the directions below, requested D2 precision before C1,
and deferred owned mode. The revision above resolves that requested
detail as a concrete design proposal. This records the supplied audit
verdict, **not** a maintainer signature or approval of the revised SHA.
The maintainer requested the RFC corrections; explicit ratification
of these new details and independent review of the revised HEAD remain
required. No C1 or implementation approval is inferred.

| ID | Auditor disposition on prior HEAD | Revised decision proposed for maintainer ratification / later gate |
| --- | --- | --- |
| D1 | ACCEPT direction | ACCEPT precise API, strict binding and resolution in §3; validate mounts/DI at C1 |
| D2 | REVISE before C1 | ACCEPT proposed v1 envelope, clear rules, restricted backend support, reservation/cold-cache caveats and golden vector in §3 only after revised audit |
| D3 | ACCEPT borrowed; DEFER owned | ACCEPT borrowed-only API and drain contract in §3; DEFER owned/factories/callbacks beyond 0.8 |
| D4 | ACCEPT | ACCEPT ABC and TTL divergence, capability/count/partial effects; descriptor and exact custom handling ratified before C2 |
| D5 | ACCEPT | ACCEPT legacy unchanged, strict opt-in direction; error classes and HTTP headers/status ratified before C3; DEFER generic timeout |
| D6 | ACCEPT | ACCEPT opt-in JSON recovery recompute uncached, no delete/write; exact allowlist/response semantics ratified before C3; DEFER broad repair |
| D7 | ACCEPT | ACCEPT trusted-only Pickle, no general recovery; concrete log categories and tests ratified before C3 |
| D8 | ACCEPT | ACCEPT evidence framework; preregister thresholds/exclusions before C4, exact-artifact expansion and risk acceptance before release |

Maintainer authorized proceeding to C1 following merge of #147. Independent delta audit reported ACCEPT on `dee1b5e6d049f6ed8d3a8be79760841a81b24feb` (35/35 checks); squash `14ad64b002aa17aa28db7325be76831de10e524f`. This accepts the design direction, not C1 implementation, later detailed decisions or release.
Record the ratifying reviewer/maintainer, disposition and exact reviewed
SHA in PR review or linked issue comment; do not self-certify a commit
from within its own contents. Any revised detail requires renewed
review. Merging prose is not acceptance or release approval.
D1–D3 resolved and ratified plus merged RFC are mandatory before C1;
D4 detailed decision before C2; D5–D7 detailed decisions before C3;
D8 performance/exclusion decisions before C4 and final evidence
before release. Each PR needs independent audit and maintainer merge
approval; no implementation scope is silently inherited.

## 11. Implementation breakdown (sequential, after RFC acceptance)

| PR | Branch / deliverable | Gate |
| --- | --- | --- |
| C1 | feat/099-app-config: opt-in handle, lifecycle and deterministic routing | D1–D3, multi-app negative tests, legacy goldens |
| C2 | refactor/111-backend-contract: capability and ownership/operation contracts | D4, real Redis + InMemory matrix, no custom ABC break |
| C3 | feat/112-failure-policy: only approved policy and serialization changes | D5–D7, negative tests, privacy and cancellation |
| C4 | test/053-100-isolation-perf: installed isolation and descriptive perf evidence | D8, no unqualified claims, full matrix |
| Release | release/0.8.0: staging, promotion, final source evidence | all accepted decisions and independent GO |

Do not close broad #111/#112 merely because a subset passed. Record residual
experimental/unsupported limitations separately. #96/#50 follow accepted
architecture later, #103 separate after 0.8, #97/#49 planned 0.9, #102
plugin/no-core unless separately qualified. No new qualification PR for
published 0.7.2 without material evidence.

## 12. Release gates

No release version or published docs change in the RFC or C1–C4.
At staging preserve 0.7.2 published identity; towncrier and promotion
only in approved release sequence. Full functional matrix, installed
security profiles, real service compatibility and exact first-attempt
Phase B on final source, strict verifier/provenance, wheel/sdist hashes,
fresh authenticated Dependabot delta and independent risk review.
TestPyPI exact-byte parity, separate maintainer authorization for PyPI
and annotated tag/GitHub Release, resolver verification and docs deploy.
No skipped required jobs, reclassified alerts without evidence, or
reuse of 0.7.2 approval. Published artifacts stay immutable.

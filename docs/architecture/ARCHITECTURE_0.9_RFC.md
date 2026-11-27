# RFC: 0.9.0 safe key filtering and tag invalidation

**Status: proposed, not released or approved for merge.** Baseline: published
0.8.0 (92380fa915ab16837a12bf9634838aae14c315a4), planning base
d6d780cb93e6c74912db90274d9a69ddacdb9e73. Refs #95, #49, #97, #53, #100, #111, #112.

## K1 — proposed narrow contract

Add keyword-only `exclude_params: Optional[Sequence[str]] = None` to
`cache`. None or empty sequence preserves the exact legacy path. Nonempty
opt-in uses the default builder only; reject a decorator-supplied custom
builder and bypass caching if the resolved configured builder is custom.
Do not cache authenticated opt-in routes with filtering; preserve existing
auth/header and explicit Request bypass. Also bypass filtering on explicit
Response parameters; never change endpoint arguments.
Validate names against the original signature, reject variadic exclusions,
duplicates, Request/Response parameters, and common identity/authorization
names as a conservative guard, not universal semantic detection. The caller
must ensure excluded dependencies do not change results, identity or access.
Do not infer safe exclusions from annotations or dependency injection. The
[K1 audit revision](KEY_FILTER_K1.md) narrows eligibility to explicit
zero-argument service dependencies and adds conservative runtime bypasses;
review that contract together with this RFC before merging K1.

Bind the original signature and apply defaults; normalize positional and
keyword spelling. For the first implementation, support exact scalar
None/bool/int/finite float/str/bytes only; bypass unsupported retained values,
variadic signatures, and binding/encoding failures rather than use repr or
silently omit dimensions. Type-tag values; preserve float signed zero.
Use a versioned SHA-256 logical key including function module/qualname,
exclusion list and retained parameter names/values. Filtered HTTP keys include
method, lowercased host, root_path and path for all routes (including generated
handlers); unfiltered routes retain the existing generated-route logic. Apply
Vary and app physical wrapping afterward. Bypass missing route identity and
non-HTTP generated/closure/wrapped handlers rather than infer safety from
object identity. Never log values. No automatic tenant
safety; #53 remains open. Rollback uses the old keys, so operators must rotate
the namespace or clear relevant old entries if source data changed.

Tests: default key goldens, positional/keyword/default equivalence, scalar
type distinctions, unsupported objects, varied hash seeds, invalid exclusions,
no mutation of arguments, auth and Request bypass, custom builders,
generated endpoints, Vary/app isolation, sync/async and Python 3.8–3.14.

## T1/T2 — tags (design questions before implementation)

Propose app scope only with exact InMemory and standalone Redis. Static,
validated literal tags; no request-derived tags in the first version.
Separate versioned index namespace, explicit app/namespace boundary, bounded
tag lengths/counts and cardinality. Decide whether namespace-scoped
invalidation uses a generation fence or atomic index registration/deletion;
compare memory, expiry, cancellation and Redis transaction/script limitations.
No implementation until reviewers agree on stale in-flight write semantics,
return counts, partial failure and unknown commit outcome. Never use global
flush, unbounded hot-path scans or cross-app tag matching.

T1 must cover overwrite, TTL, LRU eviction, clear and reverse-index cleanup
under the same lock. T2 must prove bounded index cleanup even when Redis
expires values without callbacks, atomicity/fencing across workers, failure
and cancellation behavior, and correct cleanup after rollback. No tag
support for custom/experimental adapters, Redis Cluster or legacy mode
unless separately designed and qualified. Document limits for persistent
entries and bounded work; do not silently leak metadata indefinitely.

## V1 and release

Independent installed wheel/sdist tests on supported Python and real Redis
7.4; negative privacy, clear, concurrency and rollback cases. Compare
published 0.8.0 wheel SHA256
4a7d200744424f88bfaee2a4b1fc6958e138aa86236c1906964d3cda41861bd1
with candidate options off/on; retain historical C4 baseline. Measure tag
cardinality, TTL/LRU churn and invalidation scaling; no performance
certification without #100 controlled hardware and preregistered budgets.
Keep legacy defaults and PUBLISHED_VERSION unchanged; public API docs must
continue to describe only published features until publication. Separate K1, T1, T2, V1, staging and promotion reviews.
Single-flight, events, stale, #103, HA/TLS/Cluster and new dependencies are
out of scope. No historical gate authorizes a future publication.

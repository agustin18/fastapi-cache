# C3 / D5–D7 failure policy — candidate, not released

This is the concrete C3 decision proposal for #112 on merged C2. It
requires independent audit and maintainer acceptance before merge.
No global configuration or default behavior changes.

```python
from fastapi_cache import CacheConfig, CacheFailurePolicy

config = CacheConfig(
    backend, scope_id="orders",
    failure_policy=CacheFailurePolicy(
        strict_read=True, conservative_write=True, recover_json=True
    ),
)
```

All three flags are independent, default False, immutable and scoped to
the C1 handle. Existing singleton and default scoped behavior remain
unchanged. No route override, no non-HTTP policy, no new dependencies.

| Case | Opt-in decision |
| --- | --- |
| strict_read | Exact standalone Redis ConnectionError/TimeoutError (redis-py or exact built-in ConnectionError/TimeoutError) -> sanitized CacheBackendReadError, no endpoint or write, no attached backend exception |
| Other read errors | Preserve existing fail-open recompute; fixed unclassified log for any active policy; no blanket error classification |
| conservative_write | On caught SET exception, return computed response, no library validator/304/freshness, no-store, MISS if no application-owned collision |
| recover_json | Exact JsonCoder or TypedJsonCoder, invalid UTF-8 or JSON syntax only -> recompute once uncached; no encode, set, clear or retry |
| Typed validation / tagged conversions | Propagate original errors; deferred because application validators/converters can fail for reasons unrelated to storage corruption |
| Custom coder / Pickle | Existing decode/exception behavior, no recovery or extra unpickle |
| can_encode/encode / endpoint / builder / cancellation | Unchanged, propagate exceptions |
| clear / lifecycle | C1/C2 unchanged, no policy retries or wrapping |

Strict transport allowlist uses exact classes, not subclass matching:
Redis authentication/authorization and programmer/config errors are not
silently classified as connection failures. Unknown errors retain the
default behavior, so strict_read is not a general fail-closed mode.
No retry, no generic timeout; underlying client policy is caller-owned.
A failed SET may have committed; no automatic retry or rollback.

Recovery decodes once. It distinguishes UTF-8 decoding, JSON parser
syntax, object-hook conversions and typed validation. No generic
ValueError/TypeError/ValidationError recovery; no schema/semantic
validation claim. Exact built-ins only; no subclass promotion. Pickle
still requires trusted storage; an ETag is not integrity or auth.
Explicit request no-cache revalidation retains normal recompute/store
behavior; it does not read/decode the observed value and is not a
corruption-repair algorithm. Normal GET recovery never writes or
deletes the observed entry: concurrent writers can safely replace it.
Later GETs can repeatedly recompute until expiry/operator cleanup.
No global single-flight or stale serving.

For the degraded response, the returned Response wins, otherwise the
injected Response is used. Preserve application-owned headers and status
(including ETag, Vary, cookies and preexisting cache status); append
no-store, and private for authenticated caching if absent. Existing
application directives are not stripped; no-store prohibits storage
even alongside existing freshness. No library-generated ETag or
conditional 304, no generated max-age. Set MISS only if the configured
status header is absent and not a reserved representation/control
header. Add declared Vary only if absent; existing Vary is preserved
because no cached representation is being served or created.
Application-generated 304 is not rewritten. Authentication bypass,
explicit Request/default-builder bypass and identity-aware builder
requirements remain. Log only fixed read/write/decode categories when
any policy flag is enabled; never raw key, namespace, payload, exception
text or arbitrary exception class names in this path. Legacy logs remain
unchanged; separate privacy triage if a legacy issue is verified.

Tests cover default behavior, exact built-ins, syntax/UTF-8 vs typed
validation and custom/Pickle failures, response ownership and privacy,
conditional matching, concurrent fresh write, cancellation/drain,
real Redis with injected transport failures and unknown commit outcome.
Installed wheel/sdist matrix 3.8–3.14 on Redis 7.4. Fault injection is not
network failover or latency certification. #112 remains open until
review and residual decisions are dispositioned; C4 and release separate.

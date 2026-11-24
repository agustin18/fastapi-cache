# Migrating from fastapi-cache2

`fastapi-cache-stable` is an independent, community-maintained fork of
[`fastapi-cache2`](https://pypi.org/project/fastapi-cache2/). The Python import is unchanged:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
```

The goal is a drop-in replacement for the common case: same import, same public API, same
normal success-path behavior. Bug fixes that change edge-case behavior are listed below and
are covered by regression tests. See [`COMPATIBILITY.md`](COMPATIBILITY.md) for the full
contract.

> **Release channels:** Use [PyPI](https://pypi.org/project/fastapi-cache-stable/)
> for current publications and [CHANGELOG.md](CHANGELOG.md) for historical
> versions. This guide describes the maintained behavior, not individual
> alpha/beta milestones. The installation range is Python `>=3.8,<3.14`;
> security validation covers server-side CPython 3.11–3.13, while 3.8–3.10
> are legacy functional-compatibility targets only.

## Upgrade from 0.7.0 to 0.7.1

0.7.1 is a metadata-only release published on PyPI (2026-11-24). There are no
runtime, import or public API changes from 0.7.0. It rebuilds the PyPI long
description from the corrected README so the package page no longer advertises
0.6.0. The 0.7.0 runtime corrections remain in place.

- Keep the same imports, key formats, TTL behavior and Redis contract.
- Pin `fastapi-cache-stable==0.7.1` and verify the exact artifact hashes.
- See the [0.7.1 release notes](docs/releases/RELEASE_NOTES_0.7.1.md).

## Upgrade from 0.6.0 to 0.7.0 (historical)

0.7.0 is published on PyPI (2026-11-24). There are no import or public API signature
changes from 0.6.0. The release tightens the InMemory TTL boundary to expire
at the exact deadline, decodes cached HTTP bytes before returning a
conditional `304`, and corrects Redis `get_with_ttl()` to return the
documented `(ttl, bytes-or-None)` tuple.

- Review tests for `expire=0`, negative InMemory TTLs and exact-deadline
  behavior; those values now expire immediately.
- If you return conditional `304` responses, verify malformed-cache behavior:
  invalid JSON/UTF-8/typed data fails closed instead of reaching the validator.
- Redis consumers that call `get_with_ttl()` should now receive a tuple.
- Pin the exact 0.7.0 artifact, run `pip check`, and verify MISS/HIT/304,
  authorization, variation and rollback as before.
- See the [0.7.0 release notes](docs/releases/RELEASE_NOTES_0.7.0.md) and
  [release evidence](docs/releases/RELEASE_STATUS_0.7.0.md).

## Upgrade from 0.5.0 to 0.6.0 (historical)

0.6.0 is published. Pin the version under test and verify the exact artifact. See [#92](https://github.com/agustin18/fastapi-cache/issues/92).

- Keep imports, ordinary default keys and Redis/Python bounds unchanged.
  Review opt-in private routes and their validated identity-aware key builders.
- Before traffic, rotate or selectively clear unsafe legacy namespaces and
  invalidate affected HTTP intermediary entries. Never restore unsafe private
  caching during rollback.
- Optional `InMemoryBackend(max_entries=N)` is new in 0.6.0; omit it to
  preserve unbounded behavior. It is not supported in 0.5.0.
- In a clean environment, verify the approved 0.6.0 wheel hash, install the
  local wheel by path, run `pip check` and verify distribution/import versions,
  MISS/HIT/304, authorization, variation and ordinary rollback. After actual
  PyPI verification use the exact 0.6.0 pin instead of the local path.

## Quick migration for GET, JSON and Redis/InMemory

For ordinary GET/JSON endpoints with standalone Redis or InMemory and one
startup initialization, keep the existing `fastapi_cache` imports, decorated
functions and default key builder.

1. **Inventory** your original version, backend, coder, custom key builder,
   auth/session mechanism, namespace, `clear()` calls and repeated lifespan
   initialization. Experimental backends have separate limits.
2. **Replace the dependency** `fastapi-cache2` with `fastapi-cache-stable`
   (including `[redis]` if used) and regenerate the **application's**
   requirements/lockfile so a later install cannot restore the old package.
3. **Install in a clean virtual environment**, only after your selected exact
   version is available. The old and new distribution install the same
   `fastapi_cache` module; never co-install them.
4. **Invalidate sensitive legacy data before live traffic:** selectively
   clear or rotate namespaces with old authenticated responses and old special
   `_spec_type` entries where type restoration matters. Do not flush
   unrelated Redis data. Ordinary entries can retain their keys and TTL.
5. **Verify the real application** using the checklist below. At minimum,
   anonymous MISS/HIT, authenticated bypass, headers/status, key-builder
   behavior, cache invalidation and repeated startup must be checked.
6. **Plan rollback:** returning to `fastapi-cache2==0.2.2` removes the new
   default auth bypass. Do not reenable private endpoint caching on shared
   keys; disable it or configure a safe identity-aware key builder.

"Drop-in" means a tested common path, not universal zero-change compatibility.
See [Behavior changes](#behavior-changes-in-030),
[Application verification](#application-verification-before-traffic),
and [Rollback](#rollback).

## Legacy Python security when migrating

Python 3.8–3.10 is a **functional migration bridge**, not a
security-supported deployment. Replacing `fastapi-cache2` does not
automatically remove vulnerabilities in FastAPI/Starlette/AnyIO or your
application's other dependencies. For any vulnerable dependency,
exposure depends on the installed version and the code the application
actually executes; both distributions do **not** necessarily resolve
identical versions. For production, prefer CPython 3.11–3.13 with
compatible patched dependency versions.

In Python 3.8/3.9, verified legacy profiles include AnyIO 4.5.2 and
Starlette 0.44.0 with known conditional vulnerabilities. Check
[SECURITY.md](SECURITY.md) and the
[legacy advisory guide](audit/security/LEGACY_SUPPORT_AND_RISKS.md) before
deciding whether to remain on these interpreters.

**Redis client versions:** the actually **published** `fastapi-cache2==0.2.2`
and this fork both declare `redis ^4.2.0rc1` (redis-py 4.x). The upstream
repository's later, *unreleased* `main` branch switched to redis-py 5.x.
`0.3.1` remains the previous migration line and retains redis-py 4.x. Published
`0.7.0` inherits Python-conditional metadata tested against real
standalone servers; it does not change RedisBackend runtime semantics.

## Redis client upgrade checklist for 0.7.0

The published `0.7.0` metadata admits Redis client versions according to
the supported Python interpreter:

| Python | Optional redis-py range |
|---|---|
| 3.8 | `>=4.2.0rc1,<6.2` |
| 3.9 | `>=4.2.0rc1,<7.1` |
| 3.10–3.13 | `>=4.2.0rc1,<8.2` |

- Upgrade the consumer's Redis client within the matching Python window; keep
  `decode_responses=False` for the cache backend's binary payloads.
- Confirm application-installed dependencies with `pip check`, not only
  `poetry check --lock` in this repository.
- Compare anonymous and authorized MISS/HIT, variant/tenant isolation,
  namespace clear and expired entries with the baseline client 4.6.0.
- If upgrading to redis-py 8, exercise RESP2 and RESP3 and check any other
  client consumers sharing the Redis connection.
- Retain a tested rollback pin (e.g. redis-py 4.6.0) and verify previous
  cached entries remain readable before and after reverting.
- Redis Cluster namespace clear remains `NotImplementedError`. TLS, Sentinel,
  Cluster/failover and managed-provider transports are not certified by #47.

## Who should migrate

- You are migrating `fastapi-cache2==0.2.2` to a version supported by the documented Python matrix.
- Python 3.8–3.10 remain legacy functional-compatibility targets. They are EOL and do not
  receive a stable security-support commitment; Python 3.11–3.13 form the security-supported
  matrix.
- You use `InMemoryBackend` or `RedisBackend` (standalone Redis).
- Your endpoints are GET and return JSON, Pydantic models, dataclasses or standard types.
- You need a maintained package without changing the `fastapi_cache` import.

Python 3.8/3.9/3.10 and Pydantic v1 are end-of-life upstream. Stable `0.4.1` preserves tested
functional compatibility for the documented Python 3.8–3.10 combinations, but those EOL
profiles receive no security-support promise. Any critical advisory still requires an
applicability assessment; EOL status alone does not close it. A critical advisory applicable to
package-controlled behavior must be mitigated; application-selected paths require a documented
trigger, residual risk and explicit maintainer acceptance.

The default `JsonCoder` keeps the legacy decoded behavior. Pydantic v2 users can opt into
typed restoration with `TypedJsonCoder`; Pydantic v1 users keep the legacy behavior, so
migration does not require a Pydantic upgrade or application changes.

```python
from fastapi_cache import FastAPICache
from fastapi_cache.coder import TypedJsonCoder

FastAPICache.init(backend, coder=TypedJsonCoder)
```

You can also enable it per endpoint with `@cache(coder=TypedJsonCoder)`.

`TypedJsonCoder` validates cached data and propagates validation errors. It only falls back
for Pydantic v1 models and annotations that cannot be represented by a Pydantic v2 schema.

## Request-dependent cache variants (0.3.0 → 0.3.1)

**Published 0.3.0** does not automatically vary the default key by
arbitrary `Request.headers` or `Request.state`. If the endpoint's
response changes by locale, custom tenant/auth header or middleware
state that is not present in its function arguments, the same key may
replay a stale representation. `Header(...)` values passed into
function arguments can already differentiate keys, but this does not
cover hidden request context. `Authorization`/`Cookie` request bypass
remains on by default.

**Partially mitigated in 0.3.1** ([#53](https://github.com/agustin18/fastapi-cache/issues/53)):
cache reads and writes are conservatively bypassed for endpoints that
explicitly accept `Request` while using the default key builder. Apps
that need caching in those endpoints must provide a custom
**variant- and identity-safe key builder**. This may lower hit rates for
those routes; old Redis entries are not automatically deleted. Neither
the global default key digest nor the key format for ordinary
parameter-only endpoints is changed.

**Residual scope:** Published 0.7.0 includes explicit opt-in `vary_headers` and
correctly propagates `Vary` to returned responses, but arbitrary
headers/state read by hidden dependencies, ambient `contextvars`, custom
tenant/identity and user-supplied key cardinality remain the application's
responsibility and are still tracked in
[#53](https://github.com/agustin18/fastapi-cache/issues/53).
The 0.3.1 bypass cannot detect those inputs in routes that do not declare
`Request`, and a custom key builder is an explicit application contract,
not an automatic safety guarantee.

### Explicit header variation (introduced in 0.5.0)

The 0.5.0+ `@cache(vary_headers=("Accept-Language", "X-Region"))` API
addresses a narrow case: a **public** endpoint's representation depends on
those named headers, but their values do **not** appear among the function's
FastAPI-resolved parameters. This includes a declared dependency whose
value only enters middleware state or a `ContextVar`.

- Names are validated, canonicalized and deduplicated. Header lists preserve
  their order and distinguish missing from explicitly empty values. The
  actual header values are hashed, never put verbatim in Redis keys.
- Opted-in keys use `prefix:namespace:vary-v1:<digest>`, not the legacy
  key name. The global/default builder is unchanged for all other routes.
  To migrate, clear or rotate the **affected** namespace before traffic;
  old entries are not looked up by newly varied routes but remain in Redis
  until expiry or explicit cleanup. Confirm no other app still uses that
  namespace before deleting its keys.
- Configured variants emit HTTP `Vary` on MISS, HIT and 304, including
  when the endpoint returns a `Response` rather than using the injected
  response object. For returned `JSONResponse`, the generated `Vary` is
  added **after** `JsonCoder.can_encode()` and before encoding; a returned
  plain `Response` may be cached with an opt-in `PickleCoder`. An
  injected or returned `Vary` response naming undeclared fields causes
  a bypass rather than an unsafe HIT. A returned `JSONResponse` that
  already has custom headers, including `Vary`, still bypasses the
  default JSON coder. `Vary` sent *alone* by a route, proxy or middleware
  does **not** partition `FastAPICache`'s internal store.
- The original explicit-`Request`/default-builder bypass remains active
  even with `vary_headers`. Applications requiring cached `Request`
  endpoints must use a fully identity/tenant-aware custom `key_builder`.
  Authenticated requests still bypass unless safe custom opt-in is configured;
  the decorator does not allow `Authorization`, `Cookie` or
  `Proxy-Authorization` as simple vary fields.
- The app must inventory **all** dimensions affecting output. For example,
  varying `Accept-Language` alone cannot protect an endpoint also reading
  hidden tenant/role state. Context variables, request state, dependencies,
  headers added by reverse proxies and non-header context are not inferred.
- The name validation forbids **only** `Authorization`, `Cookie` and
  `Proxy-Authorization` as credential-related names. Custom credential
  fields such as `X-API-Key` are syntactically permitted but are **not**
  automatically safe and do not trigger the default auth bypass. Use
  validated identity and permissions in a complete custom key builder,
  or bypass caching for such endpoints. Never rely on an untrusted client
  header alone to authorize tenant access.
- Arbitrary caller-controlled header values can generate many distinct
  cache keys and exhaust the backend. Validate/normalize accepted values,
  apply rate limits, suitable TTLs and capacity/eviction safeguards.
  SHA-256 for key identifiers hides raw header strings but is neither
  encryption, authentication nor cache-flood protection.

**Version and verification:** this API is available in published 0.5.0, 0.6.0 and 0.7.0
and is not part of 0.4.1. A successful test only proves the listed paths and
configurations, not generic cross-tenant isolation. The
[published 0.2.2→0.4.1 parity](audit/migration/PUBLISHED_022_TO_041_PHASE_A.md)
remains an independent historical baseline; the
[0.6.0 phase-B workflow](.github/workflows/migration-candidate-phase-b.yml)
passed on the final `stable` SHA and exact wheel/sdist. See
[0.6.0 release evidence](docs/releases/RELEASE_STATUS_0.6.0.md).

## Generated FastAPI routes and shared default keys (#68)

**Important for published 0.4.0:** The legacy default builder identifies an
endpoint from its module/name and `args`/`kwargs`. Two distinct closures
generated by a factory can have the same module/name and receive identical
arguments, even when one is registered at `/a` and the other at `/b`.
In that case, the second route can replay the first route's cached response.
For currently deployed 0.4.0 applications, give each generated route a
distinct explicit `@cache(namespace="...")` or provide a reviewed stable
route- and identity-aware key builder; rotate/clear potentially shared
namespaces **before accepting traffic**.

**Fixed in published 0.4.1:**
for generated FastAPI HTTP handlers, detect actual **closures** from
function code free variables and functions with explicit `__wrapped__`
metadata created by decorators such as `functools.wraps`. This includes
factory values captured in **default parameters**, where no free variables
remain and the qualified name can appear to be module-level. Handlers with
`<locals>` in `__qualname__` or a `<lambda>` name are also included.
The default decorator derives a separate SHA-256 key based on method,
host, mount root, request path and the legacy key. **Unwrapped module-level
handlers** and the exported `default_key_builder` remain byte-for-byte
unchanged. Existing module-level handlers decorated by another wrapper that sets
`__wrapped__` (including, but not limited to, closure wrappers) may also
receive newly partitioned keys. That invalidates their effective cache
warm state even if the responses were previously safe. Custom builders
remain application-controlled. New generated-route entries retain the same
namespace prefix, but **old closure-handler cache entries are intentionally
not reused**. The fix is present in published 0.4.1 and 0.5.0; confirm the version
installed in each environment.

**Limitations:** This narrowly addresses generated *HTTP route* key collisions.
It does not automatically fix direct `@cache` calls without an ASGI request,
duplicate module-level handler names, different applications sharing the
same host/path/backend prefix, or hidden locale/tenant/context inputs (#53).
Configure distinct backend prefixes for separate applications and
validate incoming Host values with `TrustedHostMiddleware` or an equivalent
reverse-proxy allowlist: Host values influence the generated-route cache
key, and arbitrary unvalidated hosts can fragment it and exhaust cache
capacity. Host is normalized for case, **not** for ports, trailing dots,
aliases or alternate spellings. Never treat the host-dependent cache key
as an authorization boundary. A route that explicitly declares `Request` still
follows the existing default-builder bypass. Old cached entries remain until
expiry or targeted namespace cleanup; do not flush shared Redis databases.

## Who should not migrate yet

- You need full Memcached or DynamoDB parity. They are experimental in `0.4.x`.
- You use Redis Cluster and need complete namespace clearing.
- You need typed restoration on Pydantic v1; the legacy decoded behavior is preserved instead.
  Pydantic v1 is end-of-life; plan an upgrade to Pydantic v2 for typed restoration and
  security fixes.
- You need tags, stale-while-revalidate, stampede protection or POST caching.
- You need automatic OpenAPI response-model inference without opting in;
  use `@cache(infer_response_model=True)` for supported return types or
  explicit `response_model=` in the FastAPI route decorator.
- You require untested `fastapi-pagination` configurations beyond
  the pinned integration profile.

## Install

Use a fresh environment and update your **application dependency declaration**
and lockfile: never install both distributions in one environment, because
they own the same `fastapi_cache` import.

For the previously published `0.4.1` release in a clean environment:

```sh
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.4.1"
python -m pip check
```

For published `0.7.0` in a clean environment:

```sh
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.7.1"
python -m pip check
python -c "import fastapi_cache; print(fastapi_cache.__version__)"
```

Omit `[redis]` if only InMemory is needed. Pin the exact tested version
before deploying. `pip check` does **not** detect the co-installation
collision; uninstall `fastapi-cache2` **before** installing the fork.

### Verify an exact wheel from TestPyPI

Use the version approved in [RELEASE_CHECKLIST.md](docs/releases/RELEASE_CHECKLIST.md)
and compare its downloaded SHA-256 with the approved CI artifact:

```sh
RELEASE_VERSION="<approved-version>"
python -m pip download --no-deps --only-binary=:all: \
  --index-url https://test.pypi.org/simple/ -d testpypi-dist \
  "fastapi-cache-stable==$RELEASE_VERSION"

python -m pip hash testpypi-dist/*.whl
# Compare the displayed SHA-256 with the approved CI artifact.

python -m pip install testpypi-dist/*.whl "redis==4.6.0"
python -m pip check
python -c "import fastapi_cache; print(fastapi_cache.__version__)"
```

This verified Redis profile uses redis-py 4.6.0. Other runtime dependencies
resolve from regular PyPI; do not mix TestPyPI and PyPI candidates via
`--extra-index-url` when verifying provenance.

## Compatibility matrix

- **Verified**: tested in CI with identified versions.
- **Version-specific**: inspect the actual published artifact and source SHA before claiming an API or tested security behavior is shipped.
- **Experimental**: interface available, coverage insufficient.
- **Unsupported**: outside the compatibility contract.

| Component | Status | Notes |
|---|---|---|
| Python 3.11–3.13 | Verified, security-supported | Main functional matrix and separate runtime security-audit profile |
| Python 3.10 | Verified legacy compatibility | Main functional tests and Pydantic v1 migration job; EOL, no security-support commitment |
| Python 3.8/3.9 | Verified legacy compatibility | Pinned FastAPI 0.111.1/Pydantic 1.10.27/2.8.2 matrix and wheel smoke; EOL, no security-support commitment |
| Python 3.14 | Unsupported for `0.4.1`, `0.5.0`, `0.6.0` and `0.7.0` | Add and pass a full matrix before announcing support |
| FastAPI | Verified with 0.111.1 and current 0.x | Older 0.100.x is unverified; no upper pin yet (`fastapi = "*"`) |
| Pydantic 2.x | Verified | Typed restoration is opt-in via `TypedJsonCoder`; default `JsonCoder` keeps legacy behavior |
| Pydantic v1 | Verified for migration | Tested with 1.10.27; EOL, no new security fixes; typed restoration is not applied |
| `Response`/`JSONResponse` annotations | Legacy decoded behavior | No Pydantic schema generation; cache hits keep working |
| Redis standalone | Verified for documented profiles | Published 0.4.1, 0.5.0, 0.6.0 and 0.7.0 retain Python-specific redis-py constraints: 3.8 `<6.2`, 3.9 `<7.1`, 3.10–3.13 `<8.2`, each with redis-py 4.x fallback. Real Redis server/client matrix covers the selected combinations; it does not certify all server configurations |
| Redis Cluster | Unsupported | `clear` limitations documented; no complete namespace clearing |
| InMemory | Verified for basic operations, clear semantics, `expire=None`, instance isolation and opt-in entry-count bound | Published 0.7.0 includes immutable per-instance `max_entries` (positive integer); default unbounded. An entry count is not a byte-memory cap |
| Memcached | Experimental | No full `clear`/TTL parity |
| DynamoDB | Experimental | `clear` is not implemented; the client cleanup issue remains open and is targeted for a future fix |
| Import `fastapi_cache` | Verified | Covered by compatibility tests |

> The published 0.7.0 Redis extra has **Python-conditional redis-py ranges**
> (`>=4.2.0rc1,<6.2` on 3.8; `<7.1` on 3.9; `<8.2` on 3.10–3.13).
> Qualification covers documented redis-py 4.x–8.1.x/client and Redis server
> combinations, not every configuration; see [COMPATIBILITY.md](COMPATIBILITY.md)
> and the exact release matrix. Redis Cluster namespace clear is unsupported.

## Behavior changes in 0.3.0

These intentional fixes are covered by regression tests. Version-by-version
history belongs in [CHANGELOG.md](CHANGELOG.md), not in this upgrade guide.

| Change | Original library | Maintained behavior |
|---|---|---|
| Error responses | A cached 404 could be returned as 200 | Responses with status >= 400 are not cached |
| Typed JSON decode | Cache hits returned plain dicts/lists | Opt-in `TypedJsonCoder` on Pydantic v2; default `JsonCoder`, Pydantic v1 and unsupported annotations keep the legacy decoded behavior; validation errors propagate |
| Authenticated requests | Two users could share a cache key | Requests with a non-empty `Authorization` or `Cookie` header bypass the cache by default; other authentication/session mechanisms are not detected automatically. Opt in with `cache_authenticated=True` and a safe `key_builder` |
| ETag | `hash()` changes per process; header unquoted | Stable SHA-256 digest, quoted weak ETag, weak `If-None-Match` comparison including lists and `*` |
| `clear(key=...)` | Deleted the whole prefix namespace | Deletes only that key; pass the full key |
| Namespace boundary | `clear("app:user")` also deleted `app:users` | Requires the `:` boundary |
| Redis Cluster namespace clear | Partial/unsafe clearing | Raises `NotImplementedError`; use key-only clear or flush out of band |
| `expire=None` in InMemory | Expired almost immediately | Means no expiration; `get_with_ttl` returns `-1` |
| `Cache-Control` | Could emit `max-age=None` or `max-age=-1` | Only valid values; `max-age` is omitted when no valid expiry exists |
| Request `Cache-Control` directives | Combined or case-varied `no-cache`/`no-store` directives could be ignored | Directive names are parsed case-insensitively across comma-separated and repeated fields; `no-cache` recomputes and refreshes the entry, while `no-store` bypasses this decorator cache for the request |
| `_spec_type` | User payloads with that key raised `TypeError` | Internal marker is namespaced as `__fastapi_cache_spec_type__`; user data is preserved |
| Response caching | Streaming/file/redirect and metadata-bearing `JSONResponse` could be cached incorrectly | `JsonCoder` caches only simple `200`/`application/json` `JSONResponse`; other responses bypass; `PickleCoder` bypasses streaming/file/template; `Set-Cookie`, `Cache-Control: no-store/private` and background tasks never cache |
| Second `init` | Silent no-op | Reconfiguration is explicit: `reset()` or `force=True` |

A request `Cache-Control: no-store` bypasses lookup and storage; a request
`no-cache` recomputes and refreshes the value. The decorator does not
independently revalidate a cache entry against an upstream origin.

### Authenticated requests

The legacy library cached requests with `Authorization`/`Cookie` using the
default key. The maintained implementation bypasses the cache for a non-empty
`Authorization` or `Cookie` header. Public requests keep caching. Functions decorated
without a `Request` parameter have no HTTP identity context and keep using the cache.

To cache authenticated responses, opt in explicitly and provide a key builder that includes
the identity. The key builder must include every dimension that affects the response: token,
session, tenant, permissions, and any other validated principal state. Prefer the principal
your application already validated over raw headers. Do not put credentials in plaintext in
keys or logs; use HMAC-SHA256 with an application secret.

```python
import hashlib
import hmac
import json
import os

from fastapi import Request
from starlette.exceptions import HTTPException

CACHE_KEY_SECRET = os.environ["CACHE_KEY_SECRET"].encode()


def identity_key_builder(
    func,
    namespace: str = "",
    *,
    request=None,
    response=None,
    args,
    kwargs,
):
    # This example is ONLY for the parameterless GET /me route below.
    if (
        request is None
        or request.method != "GET"
        or request.scope["path"] != "/me"
        or request.url.query
        or args
        or kwargs
    ):
        raise HTTPException(status_code=400, detail="Unsupported cache context")

    # Application authentication/authorization must populate this BEFORE
    # cache lookup, reject ambiguous credentials and check permissions.
    # Tuple of validated subject, tenant, session context, permission
    # revision, and representation revision; never raw credential headers.
    identity = getattr(request.state, "verified_cache_identity", None)
    if (
        not isinstance(identity, tuple)
        or len(identity) != 5
        or any(not isinstance(part, str) or not part for part in identity)
    ):
        raise HTTPException(status_code=403, detail="Missing verified identity")

    material = json.dumps(
        ["me-v1", namespace, func.__module__, func.__qualname__, identity],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    digest = hmac.new(
        CACHE_KEY_SECRET, material.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{namespace}:me-v1:{digest}"
```

Use the builder only on this reviewed route (not globally). Authentication
and authorization middleware or dependencies must provide the verified tuple,
including permission and representation changes, before cache lookup.
This is an illustrative contract, not authentication middleware or a generic
key builder. Anonymous requests, unsupported parameters and missing identity
are rejected by this example; use an undecorated endpoint if that is not
appropriate. Include every additional representation dimension for other
routes; do not just concatenate raw headers, trust client-provided tenant IDs,
or hash stored credentials. Use a strong secret and a fresh namespace.

```python
from fastapi_cache.decorator import cache


@app.get("/me")
@cache(
    expire=60,
    namespace="private-me-v1",
    cache_authenticated=True,
    key_builder=identity_key_builder,
)
async def me(request: Request):
    ...  # Return only data authorized for the verified identity.
```

If `cache_authenticated=True` is used with the default key builder, an authenticated request
raises `ValueError` before the cache is accessed. A custom key builder alone does not opt in;
the explicit flag is required.

The automatic bypass only detects `Authorization` and `Cookie`. Applications that use
`X-API-Key`, proxy-injected headers, `request.state`, or internal dependencies must review
their cache strategy. `cache_authenticated=True` does not make an unsafe key builder safe.
Every non-empty cookie bypasses caching by default, including anonymous analytics, consent or
preference cookies. This is intentionally conservative and can reduce cache hits on public pages.
Do not ignore a cookie in a custom key builder unless it cannot affect the response.

The 0.7.0 release protects the application cache and additionally checks every Authorization/Cookie field occurrence
and generates `Cache-Control: private, no-store` for cached HTTP responses
on authenticated-cache opt-in routes (including anonymous requests to
those routes). This does not replace application authorization or cache
policy on bypassed responses, nor purge previously stored intermediary
responses. Invalidate affected intermediary caches before migration.

**Action required when migrating from the legacy library or early prereleases:** entries written for
authenticated requests may remain under the old default key. The bypass only affects new
requests. Before deploying, clear or rotate the cache namespace, including all
instances/workers and persistent Redis caches. A public request could otherwise read an old
private entry.

### InMemory expiration and isolation

In the original library, `expire=None` can expire immediately and
`_store`/`_lock` are shared across instances. The maintained implementation:

- `expire=None` means no expiration; `get_with_ttl` returns `-1`, matching Redis/DynamoDB.
- Each backend instance owns its store and lock. A new backend after `FastAPICache.reset()`
  starts empty. Do not share one instance across event loops or threads; use one instance per
  loop/thread. Subclasses that override `__init__()` must call `super().__init__()`.
- `expire=0` keeps the legacy `or` fallback: it uses the global `expire` value. It is not
  a new "no expiration" or "expire immediately" switch.
- `FastAPICache.reset()` resets configuration, not cache data.
- InMemory remains process-local; use Redis/Memcached for cross-process sharing.

The decorator now omits `max-age` when the effective expiry is unknown (`expire=None`) or
negative, including no-expiration InMemory hits (`ttl=-1`). `ETag` and the cache-status
header are still emitted.

No data-format migration is needed: InMemory data is process-local and is lost on restart.
If you relied on class-level sharing between instances, use a shared backend instead.

### ETag and conditional requests

ETags are quoted weak validators derived from a stable SHA-256 digest of the cached
representation: `W/"<hex>"`. The value is stable across worker processes. `If-None-Match`
uses weak comparison, so `W/"<digest>"` and `"<digest>"` both match; comma-separated lists
and `*` are supported. Conditional requests are evaluated against the generated
representation on both cache hits and misses, including after `Cache-Control: no-cache`.
Malformed entity-tags are ignored. A matching conditional GET returns `304 Not Modified`
with the ETag and cache-status headers and no body. The ETag value changes once when
upgrading from the legacy library because the format changed; clients revalidate and receive
the new value.

The default key-builder implementation and its argument shape are unchanged from
`fastapi-cache2 0.2.2`; matching prefix, namespace, function and arguments continue to address
the same ordinary entries. The ETag format change does not require flushing backend data.

### `_spec_type` and user payloads

The internal marker is now `__fastapi_cache_spec_type__` instead of `_spec_type`. User
payloads that contain `_spec_type` are preserved as normal data. The decoder only interprets
the namespaced marker when the object contains exactly the marker and `val`; any other shape
is returned unchanged. Old cached entries written with the `_spec_type` marker are no longer
converted to `datetime`/`date`/`Decimal`; flush the cache namespace if you rely on those
conversions.

### Non-JSON responses

`JsonCoder` only caches simple `JSONResponse` objects: status `200`, media type
`application/json`, no custom headers, and no background task. `StreamingResponse`,
`FileResponse`, `RedirectResponse`, plain `Response`, template responses, and `JSONResponse`
objects with additional status/header metadata are returned directly and are not cached.
Custom coders can override `Coder.can_encode()` to opt in; `PickleCoder` caches
`JSONResponse`, plain `Response`, and `RedirectResponse` objects, and bypasses streaming,
file, and template responses. Responses with `Set-Cookie`, `Cache-Control: no-store` or
`Cache-Control: private`, or a background task are never cached, regardless of the coder.
A plain `Response` with a JSON media type is bypassed unless it is a `JSONResponse` or a
custom coder supports it. The injected `response` object is checked before a cache read and
before a write; `Set-Cookie`, `Cache-Control: no-store`/`private`, a background task, a
non-`200` status, or any header other than the automatic `content-length` bypasses the cache
for dict/list returns.

**Action required:** if you were affected by cached error responses or by `clear(key=...)`,
flush the cache namespace after upgrading. If you relied on `clear(key=...)` clearing the whole
prefix, switch to `clear()` or `clear(namespace=...)`. If you relied on `clear("app:user")`
deleting `app:users`, use the exact namespace. Redis Cluster users must use key-only clear or
flush the database out of band. Namespace clear is best-effort and not atomic. `clear()` is an
administrative operation; do not expose it to untrusted input. If the ETag changes, clients may
revalidate once. If you previously cached responses with cookies or private data, flush the
namespace as well.

### Second `init()` call

In the legacy library, a second `FastAPICache.init()` was a silent no-op:
the first configuration stayed active. The maintained implementation raises
`RuntimeError` on a second call unless deliberately reconfigured.

```python
FastAPICache.init(InMemoryBackend(), prefix="first")

# Raises RuntimeError: init() was already called
FastAPICache.init(InMemoryBackend(), prefix="second")

# Explicit replacement
FastAPICache.init(InMemoryBackend(), prefix="second", force=True)

# Or reset first
FastAPICache.reset()
FastAPICache.init(InMemoryBackend(), prefix="second")
```

**Action required:** `FastAPICache` stores one process-global configuration. A normal ASGI worker
should call `init()` once during startup; do not pass `force=True` as a routine lifespan setting.
Tests that enter the same application's lifespan more than once in one process must close any
backend resources they own and call `FastAPICache.reset()` during shutdown/fixture cleanup before
the next startup. If you deliberately replace a live configuration, close the previous backend
first and then use `force=True`. `reset()` clears configuration only; it neither closes backend
resources nor deletes cached data.

`force=True` replaces the global configuration; it does not release resources owned by the
previous backend (for example a Redis connection pool). It also does not isolate two FastAPI
applications running in the same process: the configuration stays global.

Changing the coder while reusing the same backend and namespace can leave entries in an
incompatible format. For example, `PickleCoder` bytes cannot be decoded by `JsonCoder`, and
the read raises `UnicodeDecodeError`. Flush or rotate the namespace when you change the
coder; the library does not delete data automatically.

## Step by step

1. **Inventory.** Note your `fastapi-cache2` version, backend, return types, `clear` usage,
   `key_builder`, headers and authentication.
2. **Characterization tests.** Before migrating, add tests for HIT/MISS, status codes,
   headers and return types so you can compare.
3. **Clean environment.** Create a virtualenv, uninstall `fastapi-cache2`, install
   `fastapi-cache-stable`, and verify `fastapi_cache.__version__`.
4. **Configure once.** Call `FastAPICache.init(...)` once during startup. Define prefix,
   expire, coder and key builder. Review authenticated endpoints.
5. **Run tests.** Verify error-response bypass, invalidation, authentication,
   InMemory expiry/isolation, ETags, special-type values and repeated initialization.
   Update assertions only for intentional behavior changes.
6. **Flush only affected data.** The default key formula is unchanged, and the ETag change only
   makes clients revalidate; neither requires a full namespace flush by itself. Clear or rotate
   namespaces that contain old authenticated entries before enabling the default auth bypass.
   Flush entries with old `_spec_type` date/datetime/Decimal markers if the restored type matters,
   and clear data written with an incompatible custom coder.
7. **Observe.** Compare HIT/MISS, latency, errors and memory with your baseline.
8. **Roll back if needed.** See below.

## Application verification before traffic

The synthetic Redis migration E2E and the one owner-maintained Redis/InMemory
application are useful evidence, **not proof about all downstream projects**.
Compare behavior using the exact published RC wheel once it is available.

| Scenario | What to verify |
|---|---|
| Anonymous GET + JSON | First request MISS; repeated request HIT; correct body, status and headers. |
| Different args/headers | Values that affect the response do not share a key. |
| `Depends()` with per-request DB objects | Check that fresh session `repr()` values do not cause permanent cache misses; use a custom safe builder where necessary. |
| Authorization / Cookie | Default bypass, no legacy private-entry reuse; review other auth mechanisms such as `X-API-Key`. |
| Response/coder | Typed results, error/redirect/streaming responses, `Set-Cookie`, `no-store`, background tasks and custom coders. |
| Invalidation | `clear(key=...)` deletes one full key; namespace operations respect boundaries. |
| Startup/shutdown | One `init()` per process, close/reset backend before repeated lifespan entry. |
| OpenAPI / pagination | Check the generated schema and any `fastapi-pagination` integration: upstream [#557](https://github.com/long2ice/fastapi-cache/issues/557) is **not** proven fixed. |

The default key-builder algorithm is unchanged: it uses module/function
identity and `repr()` of arguments. Never omit user/tenant/permission values
from a cache key merely to increase hits. The upstream
[`exclude_params` proposal #574](https://github.com/long2ice/fastapi-cache/pull/574)
is **not** implemented in the documented baseline.

## Rollback

```sh
pip uninstall -y fastapi-cache-stable
pip install "fastapi-cache2==0.2.2"
# clear or rotate only data that is incompatible or must be invalidated
```

Keep the previous version pinned and a backup of your configuration. Rollback does not
restore cache entries written with an incompatible coder or marker format; those entries are
regenerated. The default key formula is unchanged, so changing distributions alone does not
require clearing the namespace. Clear or rotate it for old authenticated responses or any
specific incompatible data identified during migration.

**Security warning:** `fastapi-cache2 0.2.2` does not include this fork's default
`Authorization`/`Cookie` bypass. If rollback will serve user-specific endpoints through the
cache, disable caching on those endpoints or configure an identity-aware `key_builder` before
traffic resumes. Clearing Redis removes existing entries but does not prevent the old version
from writing new shared keys.

## FAQ

**Does the import change?** No: `fastapi_cache`.
**Can I install both packages?** No, not in the same environment.
**What happens to my cached data?** The default key formula is unchanged from `fastapi-cache2`
0.2.2, so normal entries remain addressable. ETags are recalculated from the cached response
and clients revalidate. Clear or rotate namespaces containing old authenticated responses before
deploying the new bypass; flush old special-type entries if you depend on date/datetime/Decimal
conversion, or entries affected by the documented error-response/clear bugs.
**Which version should I deploy?** Choose the exact release tested in your
application. Check [PyPI](https://pypi.org/project/fastapi-cache-stable/)
and [CHANGELOG.md](CHANGELOG.md) for current publication status.

**What is still missing?** Memcached and DynamoDB remain experimental;
DynamoDB `clear` is not implemented. See [COMPATIBILITY.md](COMPATIBILITY.md)
for support boundaries.

**Is Pydantic v1 supported?** Migration compatibility only. Pydantic v1 is end-of-life
(1.10.27 is the final release) and receives no new security fixes. Typed restoration requires
Pydantic v2.
**Does stable `0.4.1` support Python 3.8–3.10?** Yes, for the documented legacy functional
matrix and installation range `>=3.8,<3.14`. Those EOL interpreters are outside the
security-support matrix; Python 3.11–3.13 are security-supported.
**Is Redis Cluster supported?** Only with the documented limitations; complete namespace
clearing is not promised.
**Are Memcached and DynamoDB supported?** Experimental until they have parity tests.
DynamoDB `clear` is not implemented and the client cleanup issue remains open.
**Is this an official successor?** No. It is an independent fork, not endorsed by the
original author.
**How do I report a bug?** Open an issue on the fork and pick the bug report form. For a
vulnerability, use [private vulnerability reporting](https://github.com/agustin18/fastapi-cache/security/advisories/new)
instead of a public issue; see [SECURITY.md](SECURITY.md).

## Known limitations in 0.4.x

- No tags, stale-while-revalidate, stampede protection or POST caching.
- A second `FastAPICache.init()` call raises `RuntimeError`; initialize once per worker.
  For a deliberate live replacement, close resources owned by the old backend before using
  `force=True`. Tests that re-enter one application's lifespan in the same process should close
  owned resources and call `FastAPICache.reset()` before the next startup. `reset()` does not
  close resources or delete cached data. See
  [Second `init()` call](#second-init-call).
- Redis standalone is verified with Redis 7 and redis-py 4.6.0; redis-py 5/6 are not
  supported by the current dependency constraint and are untested.
- No full backend parity.
- No perfect OpenAPI/`response_model` behavior.
- No memory cap in `InMemoryBackend`.
- Typed restoration is opt-in via `TypedJsonCoder` and requires Pydantic v2. Pydantic v1
  and unsupported annotations keep the legacy decoded behavior.
- Stable `0.4.1` installs on Python `>=3.8,<3.14`; Python 3.8–3.10 are legacy functional
  compatibility only and are excluded from stable security support. Python 3.11–3.13 are the
  security-supported matrix. Python 3.14 awaits a full CI matrix.
- In released `0.4.1`, the experimental DynamoDB extra is installable only on Python
  `>=3.10` and requires the patched aiohttp line (`>=3.14.4`). On Python 3.8/3.9,
  `fastapi-cache-stable[dynamodb]` does not install aiobotocore or aiohttp; Redis and InMemory
  remain the legacy backend options.
- The modern Poetry lock profile selects AnyIO `>=4.14.2` on Python `>=3.10`; the legacy
  Python 3.8/3.9 lock profile still resolves an older AnyIO because no fixed compatible release
  is available there. The existing runtime residual acceptance remains separately bounded. For
  the Poetry-installed test profile, the maintainer accepts AnyIO 4.5.2 only in isolated project
  tests using in-process clients and local services, with no requests to untrusted external hosts.
  This does not extend the security-support claim to consumer applications.
- The 24-month `1.x` support window in `SUPPORT.md` is conditional on the `1.x` release and
  a co-maintainer being in place; no multi-year promise is active today.

## Application migration checklist

Before live traffic, verify the **exact pinned distribution**:

- [ ] `fastapi-cache2` is uninstalled before installing the fork.
- [ ] Public requests produce correct MISS → HIT, TTL and response bodies.
- [ ] Key inputs include all relevant tenant, identity and result parameters.
- [ ] Legacy private/special Redis entries are selectively invalidated.
- [ ] OpenAPI, dependency injection and pagination are tested if used.
- [ ] Key and namespace invalidation, lifespan re-entry and rollback work.
- [ ] Rollback does not restore unsafe shared caching of private responses.

See [0.7.1 release evidence](docs/releases/RELEASE_STATUS_0.7.1.md) for the
published artifact record, distinct from the historical release checklist
and the earlier candidate gate log.

## Reproducing the Redis migration E2E

For a repeatable **published-to-published** Part A comparison, the CI workflow
[`Published legacy migration parity`](.github/workflows/migration-published-parity.yml)
installs `fastapi-cache2==0.2.2` and `fastapi-cache-stable==0.4.1`
from their actual PyPI wheels in separate virtual environments. It records
the default-key golden, InMemory GET/304, legacy auth/`Request` behavior
changes, real Redis 7.4 migration and compatible ordinary-data rollback,
then tests the stable wheel with redis-py 8.1.0. See the
[bounded Part A contract](audit/migration/PUBLISHED_022_TO_041_PHASE_A.md).
This historical published-to-published comparison is **not** a test of the
new 0.7.1 release, arbitrary consumer authentication, or unrestricted
rollback. The independent [0.7.1 phase-B workflow](.github/workflows/migration-candidate-phase-b.yml)
built the actual release wheel and sdist from the final source SHA,
recorded their SHA-256, installed each in isolated environments across
Python 3.8–3.13, ran Redis 7.4 migration, physically replaced the
candidate with the upstream 0.2.2 package for bounded ordinary-data
rollback, then ran a separate 0.7.1 InMemory/Vary consumer. See
[#69](https://github.com/agustin18/fastapi-cache/issues/69) and
[0.7.0 release evidence](docs/releases/RELEASE_STATUS_0.7.0.md).


The manual harness in [`tests/migration_redis_e2e.py`](tests/migration_redis_e2e.py) runs a legacy
writer, a candidate reader and a legacy rollback reader in separate Python processes. It covers
ordinary persisted entries and TTL, an authenticated entry that requires targeted invalidation,
the legacy `_spec_type` marker, the new auth bypass, `no-cache` refresh, preservation of an
unrelated namespace during targeted cleanup and rollback of compatible ordinary data.

Use a dedicated Redis 7 database, a unique prefix beginning `fastapi-cache-migration-e2e-`, and
synthetic auth values. Set `MIGRATION_E2E_CONFIRM_ISOLATED_REDIS=YES` only after confirming that
`REDIS_URL` targets a test-only Redis instance/database. The harness rejects prefixes with Redis
glob metacharacters, checks for any existing key under the prefix before seeding, and never flushes
the Redis database. Candidate namespace cleanup also verifies that an unrelated namespace witness
survives.
To validate a published release, download that exact candidate wheel and
verify its SHA-256 before installing it by path. Before publication, build
from the exact candidate source and record the locally built hash.
Use separate clean Python 3.11 venvs with FastAPI 0.111.1, Pydantic 2.8.2, Redis 4.6.0 and HTTPX
0.27.0; install `fastapi-cache2[redis]==0.2.2` in the legacy venv. Run from outside the source
checkout so imports resolve to the installed distributions. Set `REPO`, `REDIS_URL`,
`UNIQUE_PREFIX`, `LEGACY_PYTHON`, `CANDIDATE_PYTHON`, `CANDIDATE_WHEEL` and the version read from
that wheel as `CANDIDATE_VERSION`:

```sh
E2E_SCRIPT="$REPO/tests/migration_redis_e2e.py"
"$LEGACY_PYTHON" -m pip install \
  fastapi==0.111.1 pydantic==2.8.2 redis==4.6.0 httpx==0.27.0 \
  "fastapi-cache2[redis]==0.2.2"
"$CANDIDATE_PYTHON" -m pip install \
  fastapi==0.111.1 pydantic==2.8.2 redis==4.6.0 httpx==0.27.0 \
  "$CANDIDATE_WHEEL"
REDIS_URL="$REDIS_URL" MIGRATION_E2E_PREFIX="$UNIQUE_PREFIX" \
MIGRATION_E2E_CONFIRM_ISOLATED_REDIS=YES \
  "$LEGACY_PYTHON" -I "$E2E_SCRIPT" seed
REDIS_URL="$REDIS_URL" MIGRATION_E2E_PREFIX="$UNIQUE_PREFIX" \
MIGRATION_E2E_CONFIRM_ISOLATED_REDIS=YES \
MIGRATION_E2E_GENERATION=candidate \
MIGRATION_E2E_CANDIDATE_VERSION="$CANDIDATE_VERSION" \
  "$CANDIDATE_PYTHON" -I "$E2E_SCRIPT" candidate
REDIS_URL="$REDIS_URL" MIGRATION_E2E_PREFIX="$UNIQUE_PREFIX" \
MIGRATION_E2E_CONFIRM_ISOLATED_REDIS=YES \
MIGRATION_E2E_GENERATION=rollback "$LEGACY_PYTHON" -I "$E2E_SCRIPT" rollback
```

Record the source commit, wheel SHA-256, Python/dependency versions, Redis version and all three
mode results. This package-level E2E complements, but does not replace, the required owner-app
Redis and InMemory validations.

## See also

- [`COMPATIBILITY.md`](COMPATIBILITY.md) — compatibility contract.
- [`CHANGELOG.md`](CHANGELOG.md) — release notes.
- [`SUPPORT.md`](SUPPORT.md) — support policy.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`FORK_ORIGIN.md`](FORK_ORIGIN.md) — fork origin and attribution.

# Privacy and tenant safety

Caching can return the wrong representation if the key does not include **every input that influences the response**. This is not limited to the usual URL, query string or JSON body.

## Safe defaults in published 0.7.0

- Requests with **`Authorization`** or **`Cookie`** bypass caching by default.
- An endpoint that explicitly declares `Request` and uses the default key builder bypasses, rather than guessing whether hidden request state affects its response.
- Error/private/no-store responses have additional cache-bypass safeguards; review custom coders and returned `Response` behavior.
- Opt-in `vary_headers` partitions **only the request header fields you explicitly list**. It also emits HTTP `Vary` on MISS/HIT/304.

!!! danger "Custom authentication is not detected automatically"
    `X-API-Key`, `X-Auth-Token` or a tenant ID in middleware/context variables can control a response without appearing in the default cache key. Syntactically accepting an HTTP header name is **not** the same as authenticating it.

## Public locale example

This route reads a public `Accept-Language` dimension in a dependency. It is safe only if no other hidden dimension affects its response.

```python
from contextvars import ContextVar
from fastapi import Depends, Request

locale = ContextVar("public_locale", default="en")


async def choose_locale(request: Request) -> None:
    locale.set(request.headers.get("Accept-Language", "en"))


@app.get("/public-greeting", dependencies=[Depends(choose_locale)])
@cache(expire=60, namespace="public-greeting-v1",
       vary_headers=("Accept-Language",))
async def greeting():
    return {"language": locale.get()}
```

`app` and `cache` are defined in the application example. `Request` is on the dependency, not the decorated endpoint. The app is responsible for limiting/normalizing allowed language values.

## Never rely on these shortcuts

| Shortcut | Why it fails |
|---|---|
| Send an HTTP `Vary` header alone | It does not partition the library's own internal store |
| Vary only by locale but also read tenant state | Different tenants can collide |
| Exclude `current_user` from a key | May replay private data across users |
| Vary by `X-API-Key` without validation | Does not prove user identity or permissions |
| Hash request headers | Digest is not authentication, encryption or rate limiting |

## Protect against cardinality attacks

A client can send many distinct values and multiply entries. Validate and canonicalize externally supplied values, enforce limits and request rate controls, keep TTLs bounded and use backend capacity controls. The [bounded InMemory implementation](https://github.com/agustin18/fastapi-cache/pull/85) is available as an opt-in in **published 0.7.0**. Its entry-count limit does not replace header normalization, identity-aware cache keys, authorization checks or rate limiting.

For private/tenant-sensitive caching, prefer an application-reviewed custom key builder incorporating **validated identity, permissions and all response dimensions**, or bypass caching.

## 0.7.0 authentication and HTTP cache boundaries

The 0.7.0 correction checks all Authorization/Cookie header
occurrences and keeps generated Cache-Control private, no-store on
cached HTTP responses from routes with authenticated caching enabled
(including MISS/HIT/304). This is an HTTP intermediary policy, not a
replacement for an identity-aware server-side cache key. It is not
available in the published 0.7.0 artifact. Applications must reject
ambiguous credentials and authorize before cache lookup. For bypassed
responses, the application remains responsible for HTTP cache headers.

Do not rely on dynamic response headers evaluated after a cache lookup
to prevent replay of an older shared entry. Bypass private caching unless
the identity and permissions are explicitly captured in an appropriate
key. Rotate or purge historical affected namespaces and intermediary
entries before migration. Cache configuration is process-global; do not
share/reinitialize it between unrelated applications that require isolation.

**Full contract:** [SECURITY.md](https://github.com/agustin18/fastapi-cache/blob/stable/SECURITY.md) · [#53 residual investigation](https://github.com/agustin18/fastapi-cache/issues/53).

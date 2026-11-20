# fastapi-cache-stable 0.3.1 — security/correctness patch

`0.3.1` is a patch release for the published `0.3.0` stable line.
It does not add features, change the Python/Redis support ranges or
alter the default cache-key digest for ordinary parameter-only routes.

## Request-dependent cache variants

The default key builder hashes the endpoint identity and its function
arguments. It cannot see values read indirectly from `Request.headers`,
`Request.state` or middleware. A route whose response varied with such
values could therefore replay a cached response from a request with
different headers.

In `0.3.1`, an endpoint that **explicitly declares `Request`** and uses
the **default key builder** bypasses cache reads and writes. Endpoints
using a custom key builder keep caching and remain responsible for
including every response-defining dimension (user, tenant, locale,
content negotiation and hidden dependency inputs). FastAPI `Header(...)`
parameters already present in the function arguments remain represented
in the key and keep their normal HIT/MISS behavior.

This is a deliberate behavior change: affected routes may lose cache
hits until they adopt a reviewed custom key builder. Old cache entries
are not deleted; they remain until TTL or targeted cleanup. The internal
default key format is unchanged for other routes.

Residual limitation: this mitigation cannot detect headers or ambient
state consumed by routes that do **not** declare `Request`, nor unsafe
custom key builders. Track [#53](https://github.com/agustin18/fastapi-cache/issues/53)
for the remaining `Vary`-aware design.

## Documentation

Also includes the post-`0.3.0` publication status, release provenance,
migration/support guidance, roadmap links and tested quickstart from
[#52](https://github.com/agustin18/fastapi-cache/pull/52).

## Install

Use a fresh environment and do not co-install `fastapi-cache2`:

```sh
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.3.1"
python -m pip check
```

## Verification

- Full CI matrix for the release commit (Python 3.8–3.13 legacy/modern
  profiles, lint, types, Redis clear integration, optional backends,
  build/twine, CodeQL and security profiles).
- Consumer check on `real-estate-arg`: 46 targeted tests passed with
  published `0.3.0` and with the `0.3.1` candidate; HIT/MISS behavior
  was unchanged for its default-builder and `Request` + custom-builder
  routes. No consumer route combines a declared `Request` with the
  default builder, so this consumer loses no cache hits.
- Published wheel/sdist hashes and provenance are recorded in the
  GitHub release and release-status evidence.

These checks do not guarantee the absence of vulnerabilities in
arbitrary consumer applications. The scoped maintainer decision on
the previously accepted open GHSA remains unchanged for `0.3.x`.

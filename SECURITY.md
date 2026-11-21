# Security policy

## Supported versions

- `0.5.0` is the current published line (released **2026-11-21**). It targets
  best-effort security and critical correctness fixes on server-side
  **CPython 3.11–3.13**, within the 12-month target in
  [SUPPORT.md](SUPPORT.md) (until 2027-11-21, capacity permitting).
- `0.4.1` remains the most recent `0.4.x` patch (released **2026-11-20**),
  with the same server-side security target until 2027-11-20.
- `0.3.0` and `0.3.1` remain the previous migration line, with the
  best-effort security/critical target recorded in
  [SUPPORT.md](SUPPORT.md) (until 2027-11-19).
- Published `0.4.x` and `0.5.0` install on Python `>=3.8,<3.14`; Python 3.8–3.10 are legacy
  functional-compatibility targets only and have no security-support commitment
  for EOL runtimes or dependencies. Python 3.14 is not included until its full
  matrix passes.
- On every maintained release, critical/high findings require a scoped
  reachability assessment. If exploitable through package-controlled
  behavior, fix or block. For application-enabled features or optional
  backends, document the trigger, mitigation and residual risk.
  End-of-life status alone does not dismiss an advisory.
- `1.x`: security fixes (planned).

## Legacy interpreter risk and consumer responsibility

`0.4.x` preserves **functional compatibility** with Python 3.8–3.10 as
a migration bridge; `0.3.x` remains the previous line. That does not include security patch support for those
EOL interpreter lines or their unsupported dependencies. The preferred
production target is server-side **CPython 3.11–3.13**, plus current
compatible FastAPI/Starlette/AnyIO and other application dependencies.

On examined Python 3.8/3.9 legacy profiles, AnyIO 4.5.2 remains affected
by [GHSA-82r6-8w77-94w6](https://github.com/advisories/GHSA-82r6-8w77-94w6)
(TLS hostname/certificate handling) and Starlette 0.44.0 by
[GHSA-7f5h-v6xp-fcq8](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8)
(`FileResponse` Range DoS). We do not call the vulnerable AnyIO TLS
route or serve files in the core cache package. The removed Redis example
`StaticFiles` mount does **not** remove application-owned file-serving,
form-parsing or other Starlette risks. A consumer still must secure its
own dependency graph and routes. See
[legacy compatibility and known advisories](audit/security/LEGACY_SUPPORT_AND_RISKS.md).

**Using the original fastapi-cache2 does not automatically avoid those
risks:** both distributions can depend on the same vulnerable transitive
packages in a given application. However, their requirement ranges differ,
so identical vulnerabilities or dependency versions cannot be assumed.
Security scans are specific to the actual installed environment.

The exact PyPI RC2 wheel was installed and audited on CPython 3.11–3.13
with all extras, with no known third-party findings **at that scan date**.
The 0.4.0 release and the historical 0.3.0 release are recorded with hashes,
CI and package-installation checks; published 0.4.1 records its own final evidence. See [0.4.1 status](docs/releases/RELEASE_STATUS_0.4.1.md),
[0.4.0 provenance](docs/releases/RELEASE_STATUS_0.4.0.md) and
[0.3.0 provenance](docs/releases/RELEASE_STATUS_0.3.0.md). These checks cannot
guarantee zero vulnerabilities in arbitrary consumer environments.
The [scoped maintainer 21-GHSA release decision](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md)
is scoped to the 0.3.x line. The 0.4.0 release re-checked the open set before
publication and found no new material findings; this does not convert those
alerts into fixed issues or accept risks on behalf of consumers. Open
Dependabot alerts remain open unless genuinely fixed.

`PickleCoder` is unsafe with untrusted cache values; do not accept
attacker-controlled pickles. Authenticated request caching requires a
tenant/user-aware key builder and application-level security review.

## Request-dependent variants (0.3.0, 0.3.1, 0.4.0 and 0.4.1)

**In published 0.3.0:** the legacy default cache key includes the endpoint
function identity and arguments, **not arbitrary values read indirectly from
`request.headers`, `request.state` or middleware**. A route whose result
depends on such values may return a cached response from an earlier request
with different headers. A FastAPI `Header(...)` parameter that is passed
to the endpoint can already distinguish keys, but not every request-derived
value appears in the signature. The built-in Authorization/Cookie bypass
does not cover all custom identity/tenant mechanisms.

**Mitigated in 0.3.1 and inherited by 0.4.0** ([#53](https://github.com/agustin18/fastapi-cache/issues/53)):
if an endpoint explicitly accepts `Request` and uses the default builder,
cache reads and writes are bypassed. Applications that need caching in
those endpoints must supply a carefully reviewed custom key builder that
separates every relevant user, tenant, locale and response variant
(including hidden dependency inputs). This mitigation does not make
arbitrary application-global, middleware or custom key builders safe; it
can reduce cache hit rates for existing Request-taking endpoints. HTTP
`Vary` alone does not automatically partition our server-side
Redis/InMemory cache. **0.3.0 users must upgrade to 0.3.1 or avoid caching
such endpoints**; the published `0.3.0` wheel itself is immutable.

## Explicit Vary and hidden-context residual scope (0.5.0)

`@cache(vary_headers=(...))` is available in published 0.5.0.
**Published 0.4.1 does not expose this API.** The feature is opt-in:
an application must explicitly list every
representation-determining request header. The default key format and
the explicit-`Request`/default-builder bypass remain unchanged.
A returned `Response` receives generated `Vary` on MISS/HIT and the
conditional 304 carries `Vary`; HTTP `Vary` alone does not partition
the server-side cache. Unlisted response `Vary` values bypass storage.

**Residual limitation (#53):** this is not generic auto-detection of
dependency/middleware state, `contextvars`, validated tenant identity
or permissions. `X-API-Key` and other custom authentication field names
are *not* blocked by syntactic validation and do not trigger the standard
Authorization/Cookie bypass. Use complete identity-aware custom builders
or bypass private caching. High-cardinality, untrusted header values can
cause backend resource exhaustion; validate and bound them before
caching. Hashing does not authenticate, encrypt or prevent cardinality
attacks. Rotate/clear pre-opt-in namespaces as documented in
[MIGRATION.md](MIGRATION.md).

**Release-specific security evidence:** the 0.5.0 release used exact-artifact
installed audits on modern Python 3.11–3.13, a fresh authenticated Dependabot
delta and an explicit scoped risk decision recorded under
[#66](https://github.com/agustin18/fastapi-cache/issues/66). The 21 historical
alerts remain open where applicable. See
[0.5.0 release status](docs/releases/RELEASE_STATUS_0.5.0.md) and
[PyPI](https://pypi.org/project/fastapi-cache-stable/) for the published artifact.

## Factory-generated route key collisions (affected 0.4.0; fixed 0.4.1)

Published `0.4.0` can cache a result under the same legacy key for
distinct factory-generated handlers that share module/name, arguments,
and namespace. Published `0.4.1` isolates these generated/wrapped handlers;
validate the installed version before relying on the fix. A later request to a different route may receive the
first route's result. Treat generated-handler caching on a shared backend
as a **correctness and potential information-isolation hazard**.
Use distinct per-route `@cache(namespace=...)` values or a reviewed
route/identity-aware builder, and expire/rotate old ambiguous entries.
The #68 correction preserves unwrapped module-level route
keys while separating generated HTTP handlers, including wrappers
using `functools.wraps` that capture data as default arguments and have
no code free variables. The fix ships in **0.4.1**, not 0.4.0.
Module-level handlers wrapped by decorators setting `__wrapped__`
may intentionally rotate to new
keys; stale shared entries are not read but may persist until expiration.
The generated-route key includes request Host (case-normalized), so
untrusted arbitrary Host values can fragment storage and create cache
resource exhaustion. Validate Host using `TrustedHostMiddleware` or
equivalent edge rules. Do not assume host isolation protects hidden
`contextvars`, tenant identity, or separate apps sharing a prefix (#53).

## Reporting a vulnerability

Use GitHub private vulnerability reporting:

https://github.com/agustin18/fastapi-cache/security/advisories/new

Do not open a public issue for security reports.

Response targets, on a best-effort basis for a single maintainer: acknowledge within about
3 business days and share a remediation plan within about 10 business days. These are
targets, not contractual guarantees; see `SUPPORT.md` for the support policy.

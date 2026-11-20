# Security policy

## Supported versions

- `0.4.1` is the current prepared patch for the `0.4.x` line; `0.4.0`
  was published **2026-11-20**. The line targets best-effort security and critical correctness fixes on
  server-side **CPython 3.11–3.13**, within the 12-month target in
  [SUPPORT.md](SUPPORT.md) (until 2027-11-20, capacity permitting).
- `0.3.0` and `0.3.1` remain the previous migration line, with the
  best-effort security/critical target recorded in
  [SUPPORT.md](SUPPORT.md) (until 2027-11-19).
- Stable `0.4.x` installs on Python `>=3.8,<3.14`; Python 3.8–3.10 are legacy
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
CI and package-installation checks; the prepared 0.4.1 patch records its own
final evidence after publication. See [0.4.1 status](docs/releases/RELEASE_STATUS_0.4.1.md),
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

## Factory-generated route key collisions (0.4.0; issue #68)

Published `0.4.0` can cache a result under the same legacy key for
distinct factory-generated handlers that share module/name, arguments,
and namespace. The prepared `0.4.1` patch isolates these generated/wrapped
handlers; validate the published artifact before relying on it. A later request to a different route may receive the
first route's result. Treat generated-handler caching on a shared backend
as a **correctness and potential information-isolation hazard**.
Use distinct per-route `@cache(namespace=...)` values or a reviewed
route/identity-aware builder, and expire/rotate old ambiguous entries.
The prospective #68 correction preserves unwrapped module-level route
keys while separating generated HTTP handlers, including wrappers
using `functools.wraps` that capture data as default arguments and have
no code free variables; it has **not been published** in 0.4.0.
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

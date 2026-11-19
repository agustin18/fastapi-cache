# Security policy

## Supported versions

- Security fixes for `0.3.x` on Python 3.11–3.13 are planned to begin with the first stable
  `0.3.0` release and follow the best-effort window in `SUPPORT.md`. No stable `0.3.x` release
  has shipped yet.
- Stable `0.3.0` installs on Python `>=3.8,<3.14`; Python 3.8–3.10 are legacy
  functional-compatibility targets only and have no security-support commitment for EOL
  runtimes or dependencies. Python 3.14 is not included until its full matrix passes.
- Before stable, critical findings in legacy profiles must be triaged for applicability,
  mitigations and residual risk. A critical finding applicable to package-controlled behavior
  must be mitigated. If an advisory requires a specific application-enabled feature or
  optional backend, document that trigger and residual risk and obtain explicit maintainer
  acceptance. EOL status alone never closes a finding.
- `1.x`: security fixes (planned).

## Legacy interpreter risk and consumer responsibility

\`0.3.x\` preserves **functional compatibility** with Python 3.8–3.10 as
a migration bridge. That does not include security patch support for those
EOL interpreter lines or their unsupported dependencies. The preferred
production target is server-side **CPython 3.11–3.13**, plus current
compatible FastAPI/Starlette/AnyIO and other application dependencies.

On examined Python 3.8/3.9 legacy profiles, AnyIO 4.5.2 remains affected
by [GHSA-82r6-8w77-94w6](https://github.com/advisories/GHSA-82r6-8w77-94w6)
(TLS hostname/certificate handling) and Starlette 0.44.0 by
[GHSA-7f5h-v6xp-fcq8](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8)
(\`FileResponse\` Range DoS). We do not call the vulnerable AnyIO TLS
route or serve files in the core cache package. The removed Redis example
\`StaticFiles\` mount does **not** remove application-owned file-serving,
form-parsing or other Starlette risks. A consumer still must secure its
own dependency graph and routes. See
[legacy compatibility and known advisories](audit/security/LEGACY_SUPPORT_AND_RISKS.md).

**Using the original fastapi-cache2 does not automatically avoid those
risks:** both distributions can depend on the same vulnerable transitive
packages in a given application. However, their requirement ranges differ,
so identical vulnerabilities or dependency versions cannot be assumed.
Security scans are specific to the actual installed environment.

The exact PyPI RC2 wheel was installed and audited on CPython 3.11–3.13
with all extras, with no known third-party findings **at the scan date**.
That is not a guarantee of zero vulnerabilities for all environments.
The [dated maintainer release-risk assessment](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md)
records the proposed scoped decisions for 21 open advisories. Open
Dependabot alerts stay open unless genuinely fixed, and acceptance of
consumer-owned risk does not equate to a code fix.

\`PickleCoder\` is unsafe with untrusted cache values; do not accept
attacker-controlled pickles. Authenticated request caching requires a
tenant/user-aware key builder and application-level security review.

## Reporting a vulnerability

Use GitHub private vulnerability reporting:

https://github.com/agustin18/fastapi-cache/security/advisories/new

Do not open a public issue for security reports.

Response targets, on a best-effort basis for a single maintainer: acknowledge within about
3 business days and share a remediation plan within about 10 business days. These are
targets, not contractual guarantees; see `SUPPORT.md` for the support policy.

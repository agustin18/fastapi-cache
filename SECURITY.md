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

## Reporting a vulnerability

Use GitHub private vulnerability reporting:

https://github.com/agustin18/fastapi-cache/security/advisories/new

Do not open a public issue for security reports.

Response targets, on a best-effort basis for a single maintainer: acknowledge within about
3 business days and share a remediation plan within about 10 business days. These are
targets, not contractual guarantees; see `SUPPORT.md` for the support policy.

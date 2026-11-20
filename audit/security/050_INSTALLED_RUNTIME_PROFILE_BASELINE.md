# 0.5.0 security work — installed runtime profile baseline

Status: evidence and automated profile expansion, **not a release signoff**.
Source HEAD: `d72410954d81c2f30be2ed08fe096f104ce7aff5` (2026-11-20).

## Evidence already verified before this PR

- Authenticated [Dependabot delta run 44799798334](https://github.com/agustin18/fastapi-cache/actions/runs/44799798334) passed: 120 baseline/current records, 21 unchanged open, no newly blocking material difference (exit code 0). This is a dated graph comparison, not an audit of every downstream application.
- [Stable CI run 44802612581](https://github.com/agustin18/fastapi-cache/actions/runs/44802612581) passed. Its **all-extras wheel** security-audit jobs succeeded on Python 3.11, 3.12 and 3.13, with 73 installed distributions, 72 audited dependencies and 0 findings logged for each profile. These results are resolver- and timestamp-specific. Each CI job publishes a 90-day evidence artifact.
- Existing `scripts/validate_security_audit.py` validates the installed inventory against pip-audit records, third-party skip restrictions, package versions and wheel metadata. Existing `poetry.lock` has **multiple Python-conditional resolutions**: finding an affected version in the file does not demonstrate that it was selected by a modern installation.
- The previous 21-alert dispositions in `audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md` are scoped historical assessments. No alert is dismissed as fixed solely because an installed modern profile is clean.

## Remaining profile gap and tests proposed here

The regular CI tests `[all]` on wheel installs for CPython 3.11–3.13. This PR adds a separate, **non-publishing** workflow that tests:

| Python | Wheel without extras | Wheel `[redis]` | Source distribution `[all]` |
|---|---|---|---|
| 3.11 | Yes | Yes | — |
| 3.12 | Yes | Yes | Yes |
| 3.13 | Yes | Yes | — |

For each matrix entry, the workflow builds wheel/sdist at the **same checkout SHA**, installs the selected artifact into a dedicated consumer venv, runs `pip check`, inventories actual installed distributions and their versions, runs `pip-audit` from a **separate auditor venv**, and applies the existing strict report validator. Evidence includes artifact SHA-256, installed metadata, freeze, profile details and JSON audit output. Each job fails on incomplete results or findings and uploads available evidence on failure.

This complements rather than duplicates existing `[all]` CI. It does **not** declare coverage for every Redis server, application-auth configuration, Python 3.14, alternate dependency resolution or managed Redis transport.

## Risk classification and release decision boundaries

- **Core/library-controlled and reachable critical/high:** reproduction, remediation and exact installed-profile regression required before release.
- **Modern transitive/optional consumer paths:** inspect specific GHSA trigger and path; the installed-profile audit must cover enabled extras. A vulnerability in application-owned Starlette/AnyIO/urllib3 use remains the consuming application's responsibility unless the library exercises the vulnerable path.
- **Python 3.8–3.10:** functional legacy migration profiles only, no security-maintenance guarantee. Preserve working installs; do not force new dependency minimums that break them merely to remove lockfile alerts.
- **Security uncertainty:** no automatic acceptance. Incomplete/inaccessible evidence blocks release; material new alerts require reachability assessment. Dependabot's publication gate remains separate.
- **Versioned 0.5.0 signoff still pending:** rerun both security workflows and installed-profile audits on the **exact final candidate SHA**, inspect generated wheel **and** sdist metadata and consumer migration, record a fresh security delta, and approve publication separately.

Refs: [#66](https://github.com/agustin18/fastapi-cache/issues/66), [#69](https://github.com/agustin18/fastapi-cache/issues/69), [#70](https://github.com/agustin18/fastapi-cache/issues/70).

# Security audit evidence

This directory contains **historical dependency snapshots and release-security triage**, not user-facing installation instructions or a claim that every recorded advisory is currently open.

- [Legacy Python/security guidance](LEGACY_SUPPORT_AND_RISKS.md):
  reader-facing compatibility matrix, known inherited risks and practical
  upgrading advice.
- [21-open-GHSA scoped maintainer decision](MAINTAINER_RISK_ACCEPTANCE_20261119.md):
  proposed release-risk dispositions and required signoff, not a GitHub
  alert dismissal.
- [Exact published RC2 wheel security audit](RC2_EXACT_PYPI_WHEEL_AUDIT_20261119.md): SHA-verified PyPI wheel, 3.11–3.13 full extras profiles, complete audit results and expiring GitHub Actions artifacts.
- [Dependency security inventory](SECURITY_DEPENDENCY_INVENTORY.md): documented scope, call-path analysis and provenance of the original pre-remediation profiles.
- [Advisory triage register](SECURITY_ADVISORY_TRIAGE.csv): reconciliation of historical GHSA records with the last captured Dependabot snapshot; individual decisions may still be pending.
- [Pre-stable security review](STABLE_RELEASE_SECURITY_REVIEW_20261119.md) and
  [95-row release-disposition ledger](STABLE_RELEASE_SECURITY_REVIEW_20261119.csv):
  **proposals for auditor and maintainer approval**, not a change to GitHub alert state.
  Run `python scripts/validate_stable_security_review.py` to detect drift.
- Raw, immutable snapshots: [2026-11-16 baseline](DEPENDABOT_ALERTS_2026-11-16.csv), [2026-11-18 02:09 UTC](DEPENDABOT_ALERTS_20261118T020910Z.csv), [2026-11-18 04:42 UTC](DEPENDABOT_ALERTS_20261118T044213Z.csv), and [2026-11-18 16:51 UTC](DEPENDABOT_ALERTS_20261118T165114Z.csv), and [authenticated 2026-11-19 03:29 UTC](DEPENDABOT_ALERTS_20261119T032907Z.csv).

**These files are evidence, not live vulnerability status.** For current alerts, check GitHub's Security tab and run the maintained reconciliation script. Historical snapshots must not be overwritten to make alerts disappear.

From the repository root:

```sh
python scripts/reconcile_dependabot_alerts.py \
  --current-snapshot audit/security/DEPENDABOT_ALERTS_20261119T032907Z.csv
```

Without `--current-snapshot`, the script queries GitHub and generates a **new timestamped** snapshot under `audit/security/` by default, together with an updated register. It requires suitable GitHub credentials. Preserve and review manual triage decisions before accepting newly generated results.

Public-facing usage and security policy remain in [README](../../README.md), [SECURITY.md](../../SECURITY.md), [compatibility guide](../../COMPATIBILITY.md), and the [release checklist](../../RELEASE_CHECKLIST.md). This archive is not included in published runtime distribution metadata.

## Current-only GHSA follow-up (RC2 published; stable pending)

[GHSA-7f5h-v6xp-fcq8](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8)
is a Starlette `FileResponse` Range-header CPU DoS affecting versions
`>=0.39.0,<0.49.1`. The 2026-11-18 saved snapshots predate the finding's incorporation
in this repository's triage; the 2026-11-19 snapshot records it. The Redis example previously mounted
`StaticFiles(directory="./")`, which was unused by its template and could
serve files from the process working directory; that mount is removed by the
follow-up PR.

An [authenticated 2026-11-19 snapshot](DEPENDABOT_ALERTS_20261119T032907Z.csv)
contains 120 alert records (21 open: 1 critical, 9 high, 9 medium, 2 low;
99 fixed). It confirms alert **#120** for this GHSA remains **open/high**.
The [95-row register](SECURITY_ADVISORY_TRIAGE.csv) now records its
`APPLICATION_CONDITIONAL` scope and the example-path mitigation while keeping
`triage_status=PENDING` for the final stable-release assessment. Legacy
Starlette remains vulnerable in downstream file-serving applications.
No old snapshot was overwritten, and no GitHub alert was dismissed.

# Security audit evidence

This directory contains **historical dependency snapshots and release-security triage**, not user-facing installation instructions or a claim that every recorded advisory is currently open.

- [Legacy Python/security guidance](LEGACY_SUPPORT_AND_RISKS.md):
  reader-facing compatibility matrix, known inherited risks and practical
  upgrading advice.
- [21-open-GHSA scoped maintainer decision](MAINTAINER_RISK_ACCEPTANCE_20261119.md):
  accepted for **0.3.0** under the documented conditions, not a global
  security fix or a dismissal of open GitHub alerts.
- [Exact published RC2 wheel security audit](RC2_EXACT_PYPI_WHEEL_AUDIT_20261119.md): SHA-verified PyPI wheel, 3.11–3.13 full extras profiles, complete audit results and expiring GitHub Actions artifacts.
- [Dependency security inventory](SECURITY_DEPENDENCY_INVENTORY.md): documented scope, call-path analysis and provenance of the original pre-remediation profiles.
- [Advisory triage register](SECURITY_ADVISORY_TRIAGE.csv): reconciliation of historical GHSA records with the last captured Dependabot snapshot; individual decisions may still be pending.
- [Pre-stable security review](STABLE_RELEASE_SECURITY_REVIEW_20261119.md) and
  [95-row release-disposition ledger](STABLE_RELEASE_SECURITY_REVIEW_20261119.csv):
  the original ledger is historical reviewed evidence. The **0.3.0
  maintainer-directed scoped decision** is recorded separately in
  [MAINTAINER_RISK_ACCEPTANCE_20261119.md](MAINTAINER_RISK_ACCEPTANCE_20261119.md);
  0.3.0 was subsequently approved, tagged and published; see the
  [post-release status](../../docs/releases/RELEASE_STATUS_0.3.0.md).
  No GitHub advisory states were fabricated as fixed.
  Run `python scripts/validate_stable_security_review.py` to detect drift.
- Raw, immutable snapshots: [2026-11-16 baseline](DEPENDABOT_ALERTS_2026-11-16.csv), [2026-11-18 02:09 UTC](DEPENDABOT_ALERTS_20261118T020910Z.csv), [2026-11-18 04:42 UTC](DEPENDABOT_ALERTS_20261118T044213Z.csv), and [2026-11-18 16:51 UTC](DEPENDABOT_ALERTS_20261118T165114Z.csv), and [authenticated 2026-11-19 03:29 UTC](DEPENDABOT_ALERTS_20261119T032907Z.csv).

**These files are evidence, not live vulnerability status.** For current alerts, check GitHub's Security tab and run the maintained reconciliation script. Historical snapshots must not be overwritten to make alerts disappear.

From the repository root:

```sh
python scripts/reconcile_dependabot_alerts.py \
  --current-snapshot audit/security/DEPENDABOT_ALERTS_20261119T032907Z.csv
```

Without `--current-snapshot`, the script queries GitHub and generates a **new timestamped** snapshot under `audit/security/` by default, together with an updated register. It requires suitable GitHub credentials. Preserve and review manual triage decisions before accepting newly generated results.

Public-facing usage and security policy remain in [README](../../README.md), [SECURITY.md](../../SECURITY.md), [compatibility guide](../../COMPATIBILITY.md), and the [release checklist](../../docs/releases/RELEASE_CHECKLIST.md). This archive is not included in published runtime distribution metadata.

## Historical GHSA #120 follow-up (stable 0.3.0 published)

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

## Read-only Dependabot delta

Compare the current alerts with the newest immutable snapshot without writing
evidence files:

```sh
python scripts/reconcile_dependabot_alerts.py \
  --delta \
  --repository agustin18/fastapi-cache
```

Use `--baseline PATH` to choose a specific snapshot and
`--current-snapshot PATH` for an offline comparison. The command never
overwrites snapshots, triage CSVs or GitHub alerts.

Exit codes:

- `0`: no material change.
- `1`: new or reopened critical/high alert, or severity escalation into
  those levels. Treat as a release gate.
- `2`: comparison incomplete (empty response, missing baseline-open record,
  unknown state/severity). Investigate the API/auth/data issue; do not read
  this as a clean result.
- `3`: a material field changed on an open high/critical alert (package,
  manifest, scope, relationship, vulnerable range or patched version).
  Review the prior risk acceptance before relying on it.

The `Dependabot delta` workflow runs manually and weekly, publishes a summary
in the Actions run, and uses the read-only `vulnerability-alerts` permission.
After investigating a new alert, capture a new immutable snapshot with the
normal reconciliation flow and update the baseline intentionally; never edit
or overwrite an old snapshot to make a delta disappear.

**Known limitation:** the current evidence model identifies alerts by GHSA.
GitHub can emit more than one alert for the same GHSA (for example, different
manifests or dependency paths), and the reconciler rejects duplicate GHSA
rows instead of merging them. Any such duplication fails visibly rather than
silently producing a green delta.


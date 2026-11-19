# Security audit evidence

This directory contains **historical dependency snapshots and release-security triage**, not user-facing installation instructions or a claim that every recorded advisory is currently open.

- [Dependency security inventory](SECURITY_DEPENDENCY_INVENTORY.md): documented scope, call-path analysis and provenance of the original pre-remediation profiles.
- [Advisory triage register](SECURITY_ADVISORY_TRIAGE.csv): reconciliation of historical GHSA records with the last captured Dependabot snapshot; individual decisions may still be pending.
- Raw, immutable snapshots: [2026-11-16 baseline](DEPENDABOT_ALERTS_2026-11-16.csv), [2026-11-18 02:09 UTC](DEPENDABOT_ALERTS_20261118T020910Z.csv), [2026-11-18 04:42 UTC](DEPENDABOT_ALERTS_20261118T044213Z.csv), and [2026-11-18 16:51 UTC](DEPENDABOT_ALERTS_20261118T165114Z.csv).

**These files are evidence, not live vulnerability status.** For current alerts, check GitHub's Security tab and run the maintained reconciliation script. Historical snapshots must not be overwritten to make alerts disappear.

From the repository root:

```sh
python scripts/reconcile_dependabot_alerts.py \
  --current-snapshot audit/security/DEPENDABOT_ALERTS_20261118T165114Z.csv
```

Without `--current-snapshot`, the script queries GitHub and generates a **new timestamped** snapshot under `audit/security/` by default, together with an updated register. It requires suitable GitHub credentials. Preserve and review manual triage decisions before accepting newly generated results.

Public-facing usage and security policy remain in [README](../../README.md), [SECURITY.md](../../SECURITY.md), [compatibility guide](../../COMPATIBILITY.md), and the [release checklist](../../RELEASE_CHECKLIST.md). This archive is not included in published runtime distribution metadata.

## Post-snapshot follow-up (before RC2)

[GHSA-7f5h-v6xp-fcq8](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8)
is a Starlette `FileResponse` Range-header CPU DoS affecting versions
`>=0.39.0,<0.49.1`. The existing saved snapshots and generated triage table
predate this follow-up. The Redis example previously mounted
`StaticFiles(directory="./")`, which was unused by its template and could
serve files from the process working directory; that mount is removed by the
follow-up PR.

The reconciliation script recognizes this GHSA as a **pending, conditional**
current-only disposition when a fresh authenticated snapshot contains it.
Do not invent an alert number, edit a historical snapshot, mark the alert
fixed, or treat removal of an example path as patching downstream Starlette.
Run a fresh capture and review its resulting row before stable promotion.

"""Fail-closed validation of the dated, proposed pre-stable GHSA decision ledger.

This validates bookkeeping against an immutable captured snapshot; it does NOT
constitute maintainer approval, a current vulnerability scan, or closure of
individual GHSA findings. Refresh this ledger whenever the source register
is reconciled with a newer authenticated Dependabot snapshot.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "audit" / "security"
TRIAGE = REVIEW_DIR / "SECURITY_ADVISORY_TRIAGE.csv"
REVIEW = REVIEW_DIR / "STABLE_RELEASE_SECURITY_REVIEW_20261119.csv"
SNAPSHOT = REVIEW_DIR / "DEPENDABOT_ALERTS_20261119T032907Z.csv"
EXPECTED_SNAPSHOT = "20261119T032907Z"
EXPECTED_SNAPSHOT_RECORDS = 120

CATEGORIES = {
    "NOT_APPLICABLE": "NO_REVIEWED_LIBRARY_CALL_PATH",
    "APPLICATION_CONDITIONAL": "APPLICATION_OR_LEGACY_CONDITIONAL",
    "DEVELOPMENT_ONLY": "DEVELOPMENT_TOOLING_ONLY",
    "EXPERIMENTAL_EXTRA": "EXPERIMENTAL_OPTIONAL_BACKEND",
    "FIXED": "FIXED_IN_CAPTURED_GRAPH",
}

SPECIAL_APPROVAL_GATES = {
    "GHSA-82r6-8w77-94w6": "RECONFIRM_PRIOR_BOUNDED_ACCEPTANCE",
    "GHSA-7f5h-v6xp-fcq8": "REQUIRES_FINAL_STARLETTE_SIGNOFF",
}

REQUIRED_REVIEW_COLUMNS = (
    "ghsa_id",
    "current_alert_number",
    "source_snapshot_id",
    "current_state",
    "current_severity",
    "current_package",
    "source_preliminary_disposition",
    "proposed_release_disposition",
    "approval_gate",
    "evidence_reference",
    "profile_scope",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"empty decision evidence: {path}")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"malformed CSV record: {path}")
    return rows


def _by_ghsa(rows: Sequence[Mapping[str, str]], name: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        ghsa = row.get("ghsa_id", "")
        if not ghsa.startswith("GHSA-"):
            raise ValueError(f"invalid GHSA in {name}: {ghsa!r}")
        if ghsa in result:
            raise ValueError(f"duplicate GHSA in {name}: {ghsa}")
        result[ghsa] = row
    return result


def validate_captured_snapshot(
    triage_rows: Sequence[Mapping[str, str]],
    snapshot_rows: Sequence[Mapping[str, str]],
) -> None:
    """Check all 120 raw alerts and require every open GHSA in canonical triage.

    The historical triage intentionally omits 25 graph-fixed-only alerts.
    Never infer that an omitted raw *open* alert is accepted or irrelevant.
    """
    if len(snapshot_rows) != EXPECTED_SNAPSHOT_RECORDS:
        raise ValueError("captured snapshot size changed; refresh audit evidence")
    raw = _by_ghsa(snapshot_rows, "raw authenticated snapshot")
    triage = _by_ghsa(triage_rows, "canonical triage")
    numbers: set[str] = set()
    for ghsa, alert in raw.items():
        if alert.get("snapshot_id") != EXPECTED_SNAPSHOT:
            raise ValueError(f"captured snapshot identity changed: {ghsa}")
        number = alert.get("alert_number", "")
        if not number.isdigit() or number in numbers:
            raise ValueError(f"invalid/duplicate raw alert number: {ghsa}")
        numbers.add(number)
        state = alert.get("state")
        if state not in {"open", "fixed"}:
            raise ValueError(f"unrecognized captured alert state: {ghsa}")
        if state == "open" and ghsa not in triage:
            raise ValueError(f"raw snapshot open GHSA absent from triage: {ghsa}")
    for ghsa, old in triage.items():
        current = raw.get(ghsa)
        if current is None:
            raise ValueError(f"triage GHSA missing from raw snapshot: {ghsa}")
        for source_field, triage_field in (
            ("snapshot_date", "snapshot_date"),
            ("snapshot_id", "current_snapshot_id"),
            ("alert_number", "current_alert_number"),
            ("state", "current_state"),
            ("cve_id", "cve_id"),
            ("severity", "current_severity"),
            ("package", "current_package"),
            ("manifest_path", "current_manifest"),
            ("vulnerable_version_range", "current_vulnerable_version_range"),
            ("first_patched_version", "current_first_patched_version"),
        ):
            if current.get(source_field, "") != old.get(triage_field, ""):
                raise ValueError(
                    f"raw snapshot disagrees with triage for {ghsa}: "
                    f"{source_field}/{triage_field}"
                )

def validate_review(
    triage_rows: Sequence[Mapping[str, str]],
    review_rows: Sequence[Mapping[str, str]],
    snapshot_rows: Sequence[Mapping[str, str]] | None = None,
) -> dict[str, int]:
    if snapshot_rows is None:
        snapshot_rows = read_rows(SNAPSHOT)
    validate_captured_snapshot(triage_rows, snapshot_rows)
    if not review_rows:
        raise ValueError("empty review ledger")
    if set(REQUIRED_REVIEW_COLUMNS) - set(review_rows[0]):
        raise ValueError("missing review columns")
    triage = _by_ghsa(triage_rows, "triage")
    reviewed = _by_ghsa(review_rows, "review")
    if triage.keys() != reviewed.keys():
        raise ValueError(
            "review does not cover exact triage: missing="
            + repr(sorted(triage.keys() - reviewed.keys()))
            + " unexpected="
            + repr(sorted(reviewed.keys() - triage.keys()))
        )
    counts: Counter = Counter()
    for ghsa, old in triage.items():
        proposed = reviewed[ghsa]
        for source_field, dest_field in (
            ("current_alert_number", "current_alert_number"),
            ("current_snapshot_id", "source_snapshot_id"),
            ("current_state", "current_state"),
            ("current_severity", "current_severity"),
            ("current_package", "current_package"),
            ("preliminary_disposition", "source_preliminary_disposition"),
            ("evidence_reference", "evidence_reference"),
            ("profile_scope", "profile_scope"),
        ):
            if old[source_field] != proposed[dest_field]:
                raise ValueError(
                    f"stale review for {ghsa}: {source_field}/{dest_field}"
                )
        if old["current_snapshot_id"] != EXPECTED_SNAPSHOT:
            raise ValueError(
                f"source snapshot changed for {ghsa}; refresh reviewed decisions"
            )
        if not old["current_alert_number"].isdigit():
            raise ValueError(f"missing captured alert number: {ghsa}")
        if not proposed["evidence_reference"].strip():
            raise ValueError(f"review lacks evidence reference: {ghsa}")
        if len(proposed["profile_scope"].strip()) < 30:
            raise ValueError(f"review lacks bounded package-path scope: {ghsa}")
        state = old["current_state"]
        if state == "fixed":
            if proposed["proposed_release_disposition"] != "FIXED_IN_CAPTURED_GRAPH":
                raise ValueError(f"fixed graph state misclassified: {ghsa}")
            if proposed["approval_gate"] != "GRAPH_STATUS_ONLY":
                raise ValueError(f"fixed graph state requires no risk acceptance: {ghsa}")
            counts["graph_fixed"] += 1
        elif state == "open":
            expected = CATEGORIES.get(old["preliminary_disposition"])
            if expected is None or expected == "FIXED_IN_CAPTURED_GRAPH":
                raise ValueError(f"unclassified open alert: {ghsa}")
            if proposed["proposed_release_disposition"] != expected:
                raise ValueError(f"open GHSA not bounded by source class: {ghsa}")
            approval = SPECIAL_APPROVAL_GATES.get(
                ghsa, "REQUIRES_MAINTAINER_SIGNOFF"
            )
            if proposed["approval_gate"] != approval:
                raise ValueError(f"open GHSA approval cannot be skipped: {ghsa}")
            if old["triage_status"] != "PENDING":
                raise ValueError(
                    f"review needs update after explicit triage status change: {ghsa}"
                )
            counts["open_pending_signoff"] += 1
            counts["open_" + old["current_severity"].lower()] += 1
        else:
            raise ValueError(f"unknown GitHub captured state for {ghsa}: {state}")
    return dict(counts)


def main() -> None:
    report = validate_review(read_rows(TRIAGE), read_rows(REVIEW), read_rows(SNAPSHOT))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

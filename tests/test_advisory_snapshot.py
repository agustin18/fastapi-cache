from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import scripts.reconcile_dependabot_alerts as reconciler
from scripts.reconcile_dependabot_alerts import (
    FIXED_DISPOSITIONS,
    PRELIMINARY_DISPOSITIONS,
    _fetch_current_alerts,
    _write_csv,
    build_current_snapshot,
    ensure_current_snapshot_target,
    reconcile_historical_alerts,
)


def _alert(
    *,
    number: int,
    ghsa_id: str,
    state: str,
    package: str,
    severity: str,
    fixed_version: str | None = None,
) -> dict[str, Any]:
    return {
        "number": number,
        "state": state,
        "security_advisory": {
            "ghsa_id": ghsa_id,
            "cve_id": None,
            "summary": f"Summary for {ghsa_id}",
        },
        "security_vulnerability": {
            "severity": severity,
            "vulnerable_version_range": "< 1.0.0",
            "first_patched_version": (
                {"identifier": fixed_version} if fixed_version else None
            ),
        },
        "dependency": {
            "package": {"name": package},
            "manifest_path": "poetry.lock",
            "scope": "runtime",
            "relationship": "transitive",
        },
        "created_at": "2026-11-13T16:56:50Z",
        "fixed_at": "2026-11-17T18:33:50Z" if state == "fixed" else None,
    }


def _historical_row(
    alert_number: int, ghsa_id: str, severity: str, package: str
) -> dict[str, str]:
    return {
        "alert_number": str(alert_number),
        "ghsa_id": ghsa_id,
        "cve_id": "",
        "severity": severity,
        "package": package,
        "lock_versions": "1.0.0",
        "lock_python_versions": ">=3.8",
        "lock_optional": "False",
        "manifest": "poetry.lock",
        "scope": "runtime",
        "relationship": "transitive",
        "vulnerable_version_range": "< 1.0.0",
        "first_patched_version": "1.0.0",
        "triage_status": "Manual applicability/exploitability review pending",
    }


def test_current_snapshot_keeps_open_and_fixed_alert_states() -> None:
    alerts = [
        _alert(
            number=10,
            ghsa_id="GHSA-vqfr-h8mv-ghfj",
            state="fixed",
            package="h11",
            severity="critical",
            fixed_version="0.16.0",
        ),
        _alert(
            number=75,
            ghsa_id="GHSA-82r6-8w77-94w6",
            state="open",
            package="anyio",
            severity="critical",
        ),
    ]

    rows = build_current_snapshot(alerts, snapshot_date="2026-11-18")

    assert len(rows) == 2
    assert rows[0]["state"] == "fixed"
    assert rows[0]["first_patched_version"] == "0.16.0"
    assert rows[1]["state"] == "open"
    assert rows[1]["package"] == "anyio"


def test_current_snapshot_rejects_duplicate_ghsa_ids_without_history() -> None:
    alerts = [
        _alert(
            number=201,
            ghsa_id="GHSA-new-open-identifier",
            state="open",
            package="new-package",
            severity="high",
        ),
        _alert(
            number=202,
            ghsa_id="GHSA-new-open-identifier",
            state="open",
            package="new-package",
            severity="high",
        ),
    ]

    with pytest.raises(ValueError, match="duplicate current GHSA"):
        build_current_snapshot(alerts, snapshot_date="2026-11-18")


def test_current_snapshot_keeps_duplicate_alert_number_validation() -> None:
    first = _alert(
        number=201,
        ghsa_id="GHSA-first-alert",
        state="open",
        package="first-package",
        severity="medium",
    )
    second = _alert(
        number=201,
        ghsa_id="GHSA-second-alert",
        state="open",
        package="second-package",
        severity="medium",
    )

    with pytest.raises(ValueError, match="duplicate current alert number"):
        build_current_snapshot([first, second], snapshot_date="2026-11-18")


def test_reconciliation_separates_current_state_from_triage_and_risk_decision() -> (
    None
):
    historical = [
        _historical_row(10, "GHSA-vqfr-h8mv-ghfj", "critical", "h11"),
        _historical_row(75, "GHSA-82r6-8w77-94w6", "critical", "anyio"),
        _historical_row(73, "GHSA-cq5v-8q36-5273", "high", "aiohttp"),
        _historical_row(
            99, "GHSA-not-in-current-snapshot", "medium", "old-package"
        ),
    ]
    current = build_current_snapshot(
        [
            _alert(
                number=10,
                ghsa_id="GHSA-vqfr-h8mv-ghfj",
                state="fixed",
                package="h11",
                severity="critical",
                fixed_version="0.16.0",
            ),
            _alert(
                number=75,
                ghsa_id="GHSA-82r6-8w77-94w6",
                state="open",
                package="anyio",
                severity="critical",
            ),
            _alert(
                number=73,
                ghsa_id="GHSA-cq5v-8q36-5273",
                state="open",
                package="aiohttp",
                severity="high",
            ),
        ],
        snapshot_date="2026-11-18",
    )

    rows = reconcile_historical_alerts(
        historical, current, snapshot_date="2026-11-18"
    )
    by_ghsa = {row["ghsa_id"]: row for row in rows}

    assert by_ghsa["GHSA-vqfr-h8mv-ghfj"]["triage_status"] == "FIXED"
    assert by_ghsa["GHSA-vqfr-h8mv-ghfj"]["current_state"] == "fixed"

    anyio = by_ghsa["GHSA-82r6-8w77-94w6"]
    assert anyio["preliminary_disposition"] == "APPLICATION_CONDITIONAL"
    assert (
        anyio["maintainer_decision"]
        == "ACCEPTED_RISK_LEGACY_RUNTIME_AND_ISOLATED_TEST_LOCK_PROFILE"
    )
    assert (
        "test residual only in isolated test environments"
        in anyio["profile_scope"]
    )
    assert "not a security claim for consumer applications" in anyio["profile_scope"]
    assert anyio["release_gate"] == "RC: preserve isolated legacy test-profile boundary"
    assert anyio["triage_status"] == "PENDING"
    assert anyio["current_state"] == "open"

    dynamo = by_ghsa["GHSA-cq5v-8q36-5273"]
    assert dynamo["preliminary_disposition"] == "EXPERIMENTAL_EXTRA"
    assert (
        dynamo["maintainer_decision"]
        == "PENDING_DYNAMODB_TRANSPORT_SMOKE_AND_RC_ARTIFACT_EVIDENCE"
    )
    assert "focused external review confirmed" in dynamo["profile_scope"]
    assert "locked aiobotocore/aiohttp transport smoke" in dynamo["remaining_action"]
    assert dynamo["triage_status"] == "PENDING"

    missing = by_ghsa["GHSA-not-in-current-snapshot"]
    assert missing["current_state"] == "not_in_current_snapshot"
    assert missing["triage_status"] == "PENDING"


def test_reconciliation_rejects_duplicate_current_ghsa_ids() -> None:
    current_alert = _alert(
        number=75,
        ghsa_id="GHSA-82r6-8w77-94w6",
        state="open",
        package="anyio",
        severity="critical",
    )
    current_rows = build_current_snapshot(
        [current_alert], snapshot_date="2026-11-18"
    )
    current_rows.append({**current_rows[0], "alert_number": "76"})

    with pytest.raises(ValueError, match="duplicate current GHSA"):
        reconcile_historical_alerts(
            [_historical_row(75, "GHSA-82r6-8w77-94w6", "critical", "anyio")],
            current_rows,
            snapshot_date="2026-11-18",
        )


def test_reconciliation_rejects_duplicate_existing_triage_ghsa_ids() -> None:
    ghsa_id = "GHSA-82r6-8w77-94w6"
    historical = [_historical_row(75, ghsa_id, "critical", "anyio")]
    current = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id=ghsa_id,
                state="open",
                package="anyio",
                severity="critical",
            )
        ],
        snapshot_date="2026-11-18",
    )
    prior = [{"ghsa_id": ghsa_id, "profile_scope": "first annotation"}]

    with pytest.raises(ValueError, match="duplicate existing triage GHSA"):
        reconcile_historical_alerts(
            historical,
            current,
            snapshot_date="2026-11-18",
            existing_triage_rows=[
                prior[0],
                {**prior[0], "profile_scope": "second"},
            ],
        )


def test_reconciliation_rejects_duplicate_historical_alert_numbers() -> None:
    historical = [
        _historical_row(75, "GHSA-82r6-8w77-94w6", "critical", "anyio"),
        _historical_row(75, "GHSA-cq5v-8q36-5273", "high", "aiohttp"),
    ]

    with pytest.raises(
        ValueError, match="duplicate historical alert number: 75"
    ):
        reconcile_historical_alerts(historical, [], snapshot_date="2026-11-18")


def test_current_only_open_advisory_is_retained_as_pending_triage() -> None:
    historical = [
        _historical_row(75, "GHSA-82r6-8w77-94w6", "critical", "anyio")
    ]
    current = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id="GHSA-82r6-8w77-94w6",
                state="open",
                package="anyio",
                severity="critical",
            ),
            _alert(
                number=119,
                ghsa_id="GHSA-48p4-8xcf-vxj5",
                state="open",
                package="urllib3",
                severity="medium",
            ),
        ],
        snapshot_date="2026-11-18",
        snapshot_id="20261118T163720Z",
    )

    rows = reconcile_historical_alerts(
        historical, current, snapshot_date="2026-11-18", snapshot_id="20261118T163720Z"
    )
    new_row = next(row for row in rows if row["ghsa_id"] == "GHSA-48p4-8xcf-vxj5")

    assert len(rows) == 2
    assert new_row["historical_alert_number"] == ""
    assert new_row["historical_triage_status"] == "NOT_IN_HISTORICAL_SNAPSHOT"
    assert new_row["current_alert_number"] == "119"
    assert new_row["preliminary_disposition"] == "APPLICATION_CONDITIONAL"
    assert "Pyodide" in new_row["profile_scope"]
    assert new_row["triage_status"] == "PENDING"


def test_reconciliation_fails_closed_for_untriaged_current_open_ghsa() -> None:
    historical = [
        _historical_row(75, "GHSA-82r6-8w77-94w6", "critical", "anyio")
    ]
    current = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id="GHSA-82r6-8w77-94w6",
                state="open",
                package="anyio",
                severity="critical",
            ),
            _alert(
                number=201,
                ghsa_id="GHSA-new-open-identifier",
                state="open",
                package="new-package",
                severity="high",
            ),
        ],
        snapshot_date="2026-11-18",
    )

    with pytest.raises(
        ValueError,
        match=(
            "current open GHSA has no historical row or current-only disposition: "
            "GHSA-new-open-identifier"
        ),
    ):
        reconcile_historical_alerts(
            historical, current, snapshot_date="2026-11-18"
        )


def test_historical_fixed_advisory_is_reopened_if_current_alert_is_open() -> (
    None
):
    historical = [_historical_row(10, "GHSA-vqfr-h8mv-ghfj", "critical", "h11")]
    current = build_current_snapshot(
        [
            _alert(
                number=10,
                ghsa_id="GHSA-vqfr-h8mv-ghfj",
                state="open",
                package="h11",
                severity="critical",
                fixed_version="0.16.0",
            )
        ],
        snapshot_date="2026-11-19",
    )

    row = reconcile_historical_alerts(
        historical, current, snapshot_date="2026-11-19"
    )[0]

    assert row["triage_status"] == "PENDING_RECHECK"
    assert row["maintainer_decision"] == "CURRENT_ALERT_REQUIRES_RECHECK"
    assert row["current_state"] == "open"


def test_current_snapshot_target_refuses_overwrite_by_default(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "DEPENDABOT_ALERTS_2026-11-18.csv"
    snapshot.write_text("existing snapshot\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        ensure_current_snapshot_target(snapshot, overwrite=False)

    ensure_current_snapshot_target(snapshot, overwrite=True)


def test_csv_writer_uses_git_clean_lf_line_endings(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.csv"

    _write_csv(snapshot, ["ghsa_id"], [{"ghsa_id": "GHSA-example"}])

    contents = snapshot.read_bytes()
    assert b"\r" not in contents
    assert contents.endswith(b"\n")


def test_reconciliation_preserves_manual_triage_fields() -> None:
    ghsa_id = "GHSA-82r6-8w77-94w6"
    historical = [_historical_row(75, ghsa_id, "critical", "anyio")]
    current = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id=ghsa_id,
                state="open",
                package="anyio",
                severity="critical",
            )
        ],
        snapshot_date="2026-11-18",
    )
    prior = [
        {
            "ghsa_id": ghsa_id,
            "preliminary_disposition": "APPLICATION_CONDITIONAL",
            "triage_status": "PENDING_RECHECK",
            "maintainer_decision": "ACCEPTED_RISK_LEGACY_ONLY_LOCK_PROFILE_PENDING",
            "profile_scope": "Python 3.8/3.9 runtime only",
            "evidence_reference": "SECURITY_DEPENDENCY_INVENTORY.md#anyio",
            "remaining_action": "Review the legacy lock-installed AnyIO 4.5.2 profile",
            "release_gate": "RC",
            "manual_override_fields": (
                "maintainer_decision;profile_scope;evidence_reference;"
                "remaining_action;release_gate"
            ),
        }
    ]

    row = reconcile_historical_alerts(
        historical,
        current,
        snapshot_date="2026-11-18",
        existing_triage_rows=prior,
    )[0]

    assert row["triage_status"] == "PENDING"
    assert (
        row["maintainer_decision"]
        == "ACCEPTED_RISK_LEGACY_ONLY_LOCK_PROFILE_PENDING"
    )
    assert row["evidence_reference"] == "SECURITY_DEPENDENCY_INVENTORY.md#anyio"
    assert row["manual_override_fields"] == (
        "maintainer_decision;profile_scope;evidence_reference;remaining_action;release_gate"
    )


def test_reconciliation_rejects_unknown_manual_override_field() -> None:
    ghsa_id = "GHSA-82r6-8w77-94w6"
    historical = [_historical_row(75, ghsa_id, "critical", "anyio")]
    current = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id=ghsa_id,
                state="open",
                package="anyio",
                severity="critical",
            )
        ],
        snapshot_date="2026-11-18",
    )

    with pytest.raises(ValueError, match="unknown manual override field"):
        reconcile_historical_alerts(
            historical,
            current,
            snapshot_date="2026-11-18",
            existing_triage_rows=[
                {
                    "ghsa_id": ghsa_id,
                    "manual_override_fields": "maintainer_decison",
                }
            ],
        )


@pytest.mark.parametrize(
    "marker",
    [";", "profile_scope;;remaining_action", "profile_scope;profile_scope"],
)
def test_reconciliation_rejects_malformed_manual_override_markers(
    marker: str,
) -> None:
    ghsa_id = "GHSA-82r6-8w77-94w6"
    historical = [_historical_row(75, ghsa_id, "critical", "anyio")]
    current = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id=ghsa_id,
                state="open",
                package="anyio",
                severity="critical",
            )
        ],
        snapshot_date="2026-11-18",
    )

    with pytest.raises(
        ValueError, match="empty|duplicate manual override field"
    ):
        reconcile_historical_alerts(
            historical,
            current,
            snapshot_date="2026-11-18",
            existing_triage_rows=[
                {
                    "ghsa_id": ghsa_id,
                    "profile_scope": "a deliberate annotation",
                    "remaining_action": "a deliberate action",
                    "manual_override_fields": marker,
                }
            ],
        )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("UNRECOGNIZED_DECISION", "invalid manual preliminary disposition"),
        (
            "FIXED",
            "manual FIXED preliminary disposition requires current state fixed",
        ),
    ],
)
def test_reconciliation_rejects_invalid_manual_preliminary_disposition(
    value: str, message: str
) -> None:
    ghsa_id = "GHSA-82r6-8w77-94w6"
    historical = [_historical_row(75, ghsa_id, "critical", "anyio")]
    current = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id=ghsa_id,
                state="open",
                package="anyio",
                severity="critical",
            )
        ],
        snapshot_date="2026-11-18",
    )

    with pytest.raises(ValueError, match=message):
        reconcile_historical_alerts(
            historical,
            current,
            snapshot_date="2026-11-18",
            existing_triage_rows=[
                {
                    "ghsa_id": ghsa_id,
                    "preliminary_disposition": value,
                    "manual_override_fields": "preliminary_disposition",
                }
            ],
        )


def test_preliminary_disposition_cannot_set_triage_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ghsa_id = "GHSA-gx76-c99x-2c96"
    monkeypatch.setitem(
        PRELIMINARY_DISPOSITIONS,
        ghsa_id,
        {
            "preliminary_disposition": "EXPERIMENTAL_EXTRA",
            "triage_status": "FIXED",
        },
    )
    historical = [_historical_row(86, ghsa_id, "medium", "aiohttp")]
    current = build_current_snapshot(
        [
            _alert(
                number=86,
                ghsa_id=ghsa_id,
                state="fixed",
                package="aiohttp",
                severity="medium",
                fixed_version="3.14.4",
            )
        ],
        snapshot_date="2026-11-18",
    )

    with pytest.raises(
        ValueError,
        match="PRELIMINARY_DISPOSITIONS must not set triage_status: " + ghsa_id,
    ):
        reconcile_historical_alerts(
            historical, current, snapshot_date="2026-11-18"
        )


def test_fixed_dependabot_state_does_not_auto_close_unreviewed_triage() -> None:
    ghsa_id = "GHSA-gx76-c99x-2c96"
    historical = [_historical_row(86, ghsa_id, "medium", "aiohttp")]
    current = build_current_snapshot(
        [
            _alert(
                number=86,
                ghsa_id=ghsa_id,
                state="fixed",
                package="aiohttp",
                severity="medium",
                fixed_version="3.14.4",
            )
        ],
        snapshot_date="2026-11-18",
    )

    row = reconcile_historical_alerts(
        historical, current, snapshot_date="2026-11-18"
    )[0]

    assert row["current_state"] == "fixed"
    assert row["preliminary_disposition"] == "EXPERIMENTAL_EXTRA"
    assert row["triage_status"] == "PENDING"


def test_reconciliation_replaces_changed_generated_values_unless_marked_manual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ghsa_id = "GHSA-6mq8-rvhq-8wgg"
    monkeypatch.setitem(
        PRELIMINARY_DISPOSITIONS,
        ghsa_id,
        {
            "preliminary_disposition": "EXPERIMENTAL_EXTRA",
            "profile_scope": "Updated generated profile boundary",
            "evidence_reference": "SECURITY_DEPENDENCY_INVENTORY.md#new-evidence",
            "remaining_action": "Review the revised package path",
            "release_gate": "RC: revised boundary check",
        },
    )
    historical = [_historical_row(18, ghsa_id, "high", "aiohttp")]
    current = build_current_snapshot(
        [
            _alert(
                number=18,
                ghsa_id=ghsa_id,
                state="open",
                package="aiohttp",
                severity="high",
            )
        ],
        snapshot_date="2026-11-18",
    )
    prior = [
        {
            "ghsa_id": ghsa_id,
            "preliminary_disposition": "NOT_APPLICABLE",
            "triage_status": "PENDING",
            "maintainer_decision": "",
            "profile_scope": "Stale generated profile boundary",
            "evidence_reference": "SECURITY_DEPENDENCY_INVENTORY.md#old-evidence",
            "remaining_action": "Stale generated action",
            "release_gate": "Stale generated gate",
            "manual_override_fields": "",
        }
    ]

    row = reconcile_historical_alerts(
        historical,
        current,
        snapshot_date="2026-11-18",
        existing_triage_rows=prior,
    )[0]

    assert row["preliminary_disposition"] == "EXPERIMENTAL_EXTRA"
    assert row["profile_scope"] == "Updated generated profile boundary"
    assert row["evidence_reference"].endswith("#new-evidence")
    assert row["remaining_action"] == "Review the revised package path"
    assert row["release_gate"] == "RC: revised boundary check"


def test_reconciliation_replaces_generated_placeholders_with_new_disposition() -> (
    None
):
    ghsa_id = "GHSA-6mq8-rvhq-8wgg"
    historical = [_historical_row(18, ghsa_id, "high", "aiohttp")]
    current = build_current_snapshot(
        [
            _alert(
                number=18,
                ghsa_id=ghsa_id,
                state="open",
                package="aiohttp",
                severity="high",
            )
        ],
        snapshot_date="2026-11-18",
    )
    prior = [
        {
            "ghsa_id": ghsa_id,
            "preliminary_disposition": "PENDING",
            "triage_status": "PENDING",
            "maintainer_decision": "",
            "profile_scope": "",
            "evidence_reference": "DEPENDABOT_ALERTS_2026-11-16.csv",
            "remaining_action": "Complete individual applicability/reachability disposition.",
            "release_gate": "RC: disposition individually; stable: reconcile row",
        }
    ]

    row = reconcile_historical_alerts(
        historical,
        current,
        snapshot_date="2026-11-18",
        existing_triage_rows=prior,
    )[0]

    assert row["preliminary_disposition"] == "NOT_APPLICABLE"
    assert row["triage_status"] == "PENDING"
    assert row["evidence_reference"].endswith("#aiohttp-client-path-review")
    assert row["remaining_action"] != prior[0]["remaining_action"]
    assert row["release_gate"] == "RC: confirm package-path boundary"


def test_every_historical_advisory_has_a_preliminary_disposition() -> None:
    historical_path = (
        Path(__file__).resolve().parents[1] / "DEPENDABOT_ALERTS_2026-11-16.csv"
    )
    with historical_path.open(encoding="utf-8-sig", newline="") as source:
        historical = list(csv.DictReader(source))

    critical_or_high_ids = {
        row["ghsa_id"]
        for row in historical
        if row["severity"].lower() in {"critical", "high"}
    }
    medium_or_low_ids = {
        row["ghsa_id"]
        for row in historical
        if row["severity"].lower() in {"medium", "low"}
    }
    classified_ids = set(PRELIMINARY_DISPOSITIONS) | set(FIXED_DISPOSITIONS)

    assert len(critical_or_high_ids) == 33
    assert len(medium_or_low_ids) == 60
    assert critical_or_high_ids | medium_or_low_ids <= classified_ids
    missing_profile_scope = [
        ghsa_id
        for ghsa_id in critical_or_high_ids | medium_or_low_ids
        if not (
            PRELIMINARY_DISPOSITIONS.get(ghsa_id)
            or FIXED_DISPOSITIONS.get(ghsa_id, {})
        ).get("profile_scope")
    ]
    assert missing_profile_scope == []


def test_aiohttp_proxy_redirect_review_stays_open_for_rc() -> None:
    ghsa_id = "GHSA-966j-vmvw-g2g9"
    historical = [_historical_row(46, ghsa_id, "low", "aiohttp")]
    current = build_current_snapshot(
        [
            _alert(
                number=46,
                ghsa_id=ghsa_id,
                state="open",
                package="aiohttp",
                severity="low",
            )
        ],
        snapshot_date="2026-11-18",
    )

    row = reconcile_historical_alerts(
        historical, current, snapshot_date="2026-11-18"
    )[0]

    assert row["preliminary_disposition"] == "EXPERIMENTAL_EXTRA"
    assert row["triage_status"] == "PENDING"
    assert (
        row["maintainer_decision"]
        == "PENDING_DYNAMODB_TRANSPORT_SMOKE_AND_RC_ARTIFACT_EVIDENCE"
    )
    assert (
        row["release_gate"]
        == "RC: verify patched DynamoDB transport and artifact evidence"
    )


def test_fetch_current_alerts_flattens_all_paginated_cli_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pages = [
        [{"number": number} for number in range(100)],
        [{"number": number} for number in range(100, 118)],
    ]
    assert len(pages) == 2
    command_result = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=0,
        stdout=json.dumps(pages),
        stderr="",
    )
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: command_result
    )

    alerts = _fetch_current_alerts("owner/repository")

    assert len(alerts) == 118
    assert alerts[0]["number"] == 0
    assert alerts[-1]["number"] == 117


def test_new_open_alert_keeps_raw_capture_without_rewriting_triage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    historical_path = tmp_path / "historical.csv"
    with historical_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(
            destination, fieldnames=reconciler.HISTORICAL_FIELDS
        )
        writer.writeheader()
        writer.writerow(
            _historical_row(75, "GHSA-82r6-8w77-94w6", "critical", "anyio")
        )
    triage_path = tmp_path / "SECURITY_ADVISORY_TRIAGE.csv"
    previous_triage = b"ghsa_id,triage_status\nGHSA-old,PENDING\n"
    triage_path.write_bytes(previous_triage)
    monkeypatch.setattr(
        reconciler,
        "_fetch_current_alerts",
        lambda repository: [
            _alert(
                number=201,
                ghsa_id="GHSA-new-open-identifier",
                state="open",
                package="new-package",
                severity="high",
            )
        ],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reconcile_dependabot_alerts.py",
            "--repository",
            "owner/repository",
            "--historical",
            str(historical_path),
            "--output-dir",
            str(tmp_path),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "current open GHSA has no historical row or current-only disposition: "
            "GHSA-new-open-identifier"
        ),
    ):
        reconciler.main()

    snapshots = list(tmp_path.glob("DEPENDABOT_ALERTS_*.csv"))
    assert len(snapshots) == 1
    captured = list(csv.DictReader(snapshots[0].open(encoding="utf-8")))
    assert captured[0]["ghsa_id"] == "GHSA-new-open-identifier"
    assert triage_path.read_bytes() == previous_triage


def test_saved_snapshot_can_regenerate_triage_without_github_api(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    historical_path = tmp_path / "historical.csv"
    with historical_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(
            destination, fieldnames=reconciler.HISTORICAL_FIELDS
        )
        writer.writeheader()
        writer.writerow(
            _historical_row(75, "GHSA-82r6-8w77-94w6", "critical", "anyio")
        )

    snapshot_path = tmp_path / "current.csv"
    current_rows = build_current_snapshot(
        [
            _alert(
                number=75,
                ghsa_id="GHSA-82r6-8w77-94w6",
                state="open",
                package="anyio",
                severity="critical",
            ),
            _alert(
                number=119,
                ghsa_id="GHSA-48p4-8xcf-vxj5",
                state="open",
                package="urllib3",
                severity="medium",
            ),
        ],
        snapshot_date="2026-11-18",
        snapshot_id="20261118T044213Z",
    )
    _write_csv(snapshot_path, reconciler.CURRENT_SNAPSHOT_FIELDS, current_rows)
    original_snapshot = snapshot_path.read_bytes()
    monkeypatch.setattr(
        reconciler,
        "_fetch_current_alerts",
        lambda repository: pytest.fail("saved-snapshot mode must not call GitHub"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reconcile_dependabot_alerts.py",
            "--current-snapshot",
            str(snapshot_path),
            "--historical",
            str(historical_path),
            "--output-dir",
            str(tmp_path),
        ],
    )

    reconciler.main()
    report = json.loads(capsys.readouterr().out)

    assert snapshot_path.read_bytes() == original_snapshot
    assert report["historical_rows"] == 1
    assert report["triage_rows"] == 2
    assert report["current_only_triage_rows"] == 1
    assert report["historical_current_open"] == 1
    assert report["current_open_not_historical"] == 1
    triage_path = tmp_path / "SECURITY_ADVISORY_TRIAGE.csv"
    with triage_path.open(encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    current_only = next(
        row for row in rows if row["ghsa_id"] == "GHSA-48p4-8xcf-vxj5"
    )
    assert current_only["historical_alert_number"] == ""
    assert current_only["historical_triage_status"] == "NOT_IN_HISTORICAL_SNAPSHOT"
    assert current_only["triage_status"] == "PENDING"
    anyio = next(row for row in rows if row["ghsa_id"] == "GHSA-82r6-8w77-94w6")
    assert anyio["current_snapshot_id"] == "20261118T044213Z"
    assert anyio["maintainer_decision"] == (
        "ACCEPTED_RISK_LEGACY_RUNTIME_AND_ISOLATED_TEST_LOCK_PROFILE"
    )


def test_adjudicated_transitive_boundaries_keep_distinct_classifications() -> (
    None
):
    host_cache = PRELIMINARY_DISPOSITIONS["GHSA-hcc4-c3v8-rx92"]
    assert host_cache["preliminary_disposition"] == "EXPERIMENTAL_EXTRA"
    assert "TCPConnector" in host_cache["profile_scope"]
    assert (
        host_cache["maintainer_decision"]
        == "PENDING_STABLE_PATCHED_PROFILE_VERIFICATION"
    )
    assert (
        host_cache["release_gate"]
        == "Stable: verify optional DynamoDB DNS cache scope"
    )

    pool_manager = PRELIMINARY_DISPOSITIONS["GHSA-pq67-6m6q-mj2v"]
    assert pool_manager["preliminary_disposition"] == "NOT_APPLICABLE"
    assert "runtime/transitive" in pool_manager["profile_scope"]

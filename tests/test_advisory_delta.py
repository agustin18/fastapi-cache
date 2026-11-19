from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import scripts.reconcile_dependabot_alerts as reconciler
from scripts.reconcile_dependabot_alerts import (
    _write_csv,
    build_current_snapshot,
    build_delta_report,
    main,
)


def _alert(
    *,
    number: int,
    ghsa_id: str,
    state: str = "open",
    severity: str = "high",
    package: str = "demo-package",
    vulnerable_range: str = "< 1.0.0",
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
            "vulnerable_version_range": vulnerable_range,
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
        "created_at": "2026-11-19T00:00:00Z",
        "fixed_at": "2026-11-19T01:00:00Z" if state == "fixed" else None,
        "dismissed_at": "2026-11-19T01:00:00Z"
        if state == "dismissed"
        else None,
        "dismissed_reason": "not_used" if state == "dismissed" else None,
    }


def _rows(alerts: list[dict[str, Any]]) -> list[dict[str, str]]:
    return build_current_snapshot(
        alerts, snapshot_date="2026-11-19", snapshot_id="20261119T000000Z"
    )


def test_delta_accepts_unchanged_accepted_open_alert() -> None:
    baseline = _rows([_alert(number=1, ghsa_id="GHSA-existing")])
    current = _rows([_alert(number=1, ghsa_id="GHSA-existing")])

    report = build_delta_report(baseline, current)

    assert report["blocking"] is False
    assert report["blocking_reasons"] == []
    assert report["unchanged_open"] == ["GHSA-existing"]
    assert report["new_open"] == []
    assert report["reopened"] == []


def test_delta_blocks_new_open_high_and_critical_alerts() -> None:
    current = _rows(
        [
            _alert(
                number=2,
                ghsa_id="GHSA-new-critical",
                severity="critical",
                package="new-package",
            )
        ]
    )

    report = build_delta_report([], current)

    assert report["blocking"] is True
    assert "new_open:GHSA-new-critical" in report["blocking_reasons"]
    assert report["new_open"][0]["package"] == "new-package"


def test_delta_reports_new_medium_alert_without_blocking() -> None:
    current = _rows(
        [_alert(number=3, ghsa_id="GHSA-new-medium", severity="medium")]
    )

    report = build_delta_report([], current)

    assert report["blocking"] is False
    assert report["new_open"][0]["severity"] == "medium"


def test_delta_blocks_reopened_high_alert() -> None:
    baseline = _rows(
        [
            _alert(
                number=4,
                ghsa_id="GHSA-reopened",
                state="fixed",
                fixed_version="2.0.0",
            )
        ]
    )
    current = _rows([_alert(number=4, ghsa_id="GHSA-reopened")])

    report = build_delta_report(baseline, current)

    assert report["blocking"] is True
    assert report["reopened"][0]["ghsa_id"] == "GHSA-reopened"
    assert "reopened:GHSA-reopened" in report["blocking_reasons"]


def test_delta_reports_fixed_changed_and_severity_escalation() -> None:
    baseline = _rows(
        [
            _alert(number=5, ghsa_id="GHSA-fixed"),
            _alert(number=6, ghsa_id="GHSA-changed"),
            _alert(
                number=7,
                ghsa_id="GHSA-escalated",
                severity="medium",
            ),
        ]
    )
    current = _rows(
        [
            _alert(
                number=5,
                ghsa_id="GHSA-fixed",
                state="fixed",
                fixed_version="2.0.0",
            ),
            _alert(
                number=6,
                ghsa_id="GHSA-changed",
                vulnerable_range="< 2.0.0",
            ),
            _alert(number=7, ghsa_id="GHSA-escalated", severity="high"),
        ]
    )

    report = build_delta_report(baseline, current)

    assert report["newly_fixed"][0]["ghsa_id"] == "GHSA-fixed"
    assert report["changed"][0]["ghsa_id"] == "GHSA-changed"
    assert report["blocking"] is True
    assert "severity_escalation:GHSA-escalated" in report["blocking_reasons"]


def test_delta_reports_auto_dismissed_as_newly_dismissed() -> None:
    baseline = _rows([_alert(number=11, ghsa_id="GHSA-auto")])
    current = _rows(
        [_alert(number=11, ghsa_id="GHSA-auto", state="auto_dismissed")]
    )

    report = build_delta_report(baseline, current)

    assert report["blocking"] is False
    assert report["newly_dismissed"][0]["ghsa_id"] == "GHSA-auto"


def test_delta_cli_is_read_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_path = tmp_path / "baseline.csv"
    _write_csv(
        baseline_path,
        reconciler.CURRENT_SNAPSHOT_FIELDS,
        _rows([_alert(number=8, ghsa_id="GHSA-existing")]),
    )
    monkeypatch.setattr(
        reconciler,
        "_fetch_current_alerts",
        lambda repository: [_alert(number=8, ghsa_id="GHSA-existing")],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reconcile_dependabot_alerts.py",
            "--delta",
            "--repository",
            "owner/repository",
            "--baseline",
            str(baseline_path),
            "--output-dir",
            str(tmp_path),
        ],
    )

    result = main()
    report = json.loads(capsys.readouterr().out)

    assert result == 0
    assert report["blocking"] is False
    assert report["unchanged_open"] == ["GHSA-existing"]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["baseline.csv"]


def test_delta_saved_snapshot_mode_does_not_fetch_or_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_path = tmp_path / "baseline.csv"
    current_path = tmp_path / "current.csv"
    _write_csv(
        baseline_path,
        reconciler.CURRENT_SNAPSHOT_FIELDS,
        _rows([_alert(number=9, ghsa_id="GHSA-existing")]),
    )
    _write_csv(
        current_path,
        reconciler.CURRENT_SNAPSHOT_FIELDS,
        _rows([_alert(number=10, ghsa_id="GHSA-new-high")]),
    )
    original_baseline = baseline_path.read_bytes()
    original_current = current_path.read_bytes()
    monkeypatch.setattr(
        reconciler,
        "_fetch_current_alerts",
        lambda repository: pytest.fail(
            "saved-snapshot delta must not call GitHub"
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reconcile_dependabot_alerts.py",
            "--delta",
            "--repository",
            "owner/repository",
            "--baseline",
            str(baseline_path),
            "--current-snapshot",
            str(current_path),
            "--output-dir",
            str(tmp_path),
        ],
    )

    result = main()
    report = json.loads(capsys.readouterr().out)

    assert result == 1
    assert report["current_source"] == str(current_path)
    assert report["blocking"] is True
    assert baseline_path.read_bytes() == original_baseline
    assert current_path.read_bytes() == original_current
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "baseline.csv",
        "current.csv",
    ]

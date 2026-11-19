"""Guard the frozen pre-stable security review against silent alert closures."""

from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.validate_stable_security_review import (
    REVIEW,
    TRIAGE,
    read_rows,
    validate_review,
)


@pytest.fixture
def evidence():
    return read_rows(TRIAGE), read_rows(REVIEW)


def test_all_95_ghsa_are_accounted_for_without_accepting_open_risk(evidence):
    triage, review = evidence
    report = validate_review(triage, review)
    assert len(triage) == len(review) == 95
    assert report == {
        "graph_fixed": 74,
        "open_pending_signoff": 21,
        "open_critical": 1,
        "open_high": 9,
        "open_medium": 9,
        "open_low": 2,
    }


def test_all_open_alerts_still_require_explicit_approval(evidence):
    triage, review = evidence
    open_reviews = [r for r in review if r["current_state"] == "open"]
    assert len(open_reviews) == 21
    assert all(r["approval_gate"] != "GRAPH_STATUS_ONLY" for r in open_reviews)
    assert all(
        r["proposed_release_disposition"] != "FIXED_IN_CAPTURED_GRAPH"
        for r in open_reviews
    )
    assert len([r for r in triage if r["triage_status"] == "PENDING"]) == 94


@pytest.mark.parametrize(
    "change,expected_error",
    [
        ("missing_row", "review does not cover exact triage"),
        ("open_called_fixed", "open GHSA not bounded by source class"),
        ("open_approval_skipped", "open GHSA approval cannot be skipped"),
        ("wrong_profile_scope", "stale review"),
        ("wrong_snapshot", "stale review"),
    ],
)
def test_rejects_unsubstantiated_release_decisions(
    evidence, change, expected_error
):
    triage, review = deepcopy(evidence)
    open_row = next(r for r in review if r["current_state"] == "open")
    if change == "missing_row":
        review.remove(open_row)
    elif change == "open_called_fixed":
        open_row["proposed_release_disposition"] = "FIXED_IN_CAPTURED_GRAPH"
    elif change == "open_approval_skipped":
        open_row["approval_gate"] = "GRAPH_STATUS_ONLY"
    elif change == "wrong_profile_scope":
        open_row["profile_scope"] = "no vulnerability"
    elif change == "wrong_snapshot":
        open_row["source_snapshot_id"] = "20261120T000000Z"
    with pytest.raises(ValueError, match=expected_error):
        validate_review(triage, review)


def test_rejects_new_open_alert_without_review(evidence):
    triage, review = deepcopy(evidence)
    newly_discovered = deepcopy(next(r for r in triage if r["current_state"] == "open"))
    newly_discovered["ghsa_id"] = "GHSA-test-new-1234"
    newly_discovered["current_alert_number"] = "999"
    triage.append(newly_discovered)
    with pytest.raises(ValueError, match="review does not cover exact triage"):
        validate_review(triage, review)


def test_rejects_reopened_graph_fixed_alert(evidence):
    triage, review = deepcopy(evidence)
    fixed = next(r for r in triage if r["current_state"] == "fixed")
    fixed["current_state"] = "open"
    with pytest.raises(ValueError, match="stale review"):
        validate_review(triage, review)

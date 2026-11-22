"""The public onboarding comparison fails closed on unsafe regressions."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from examples.migration.compare import verify


def _reports() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {
            "distribution": "fastapi-cache2",
            "version": "0.2.2",
            "public_statuses": ["MISS", "HIT"],
            "conditional_status": 304,
            "viewer_statuses": ["MISS", "HIT"],
            "viewer_results": ["alice", "alice"],
        },
        {
            "distribution": "fastapi-cache-stable",
            "version": "0.6.0",
            "public_statuses": ["MISS", "HIT"],
            "conditional_status": 304,
            "viewer_statuses": [None, None],
            "viewer_results": ["alice", "bob"],
        },
    )


def test_public_migration_demo_expected_contract() -> None:
    legacy, replacement = _reports()
    verify(legacy, replacement)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("version", "0.5.0"),
        ("public_statuses", ["MISS", "MISS"]),
        ("conditional_status", 200),
        ("viewer_statuses", ["MISS", "HIT"]),
        ("viewer_results", ["alice", "alice"]),
    ],
)
def test_comparator_rejects_false_security_or_release_claims(
    field: str, bad_value: object
) -> None:
    legacy, replacement = _reports()
    replacement = deepcopy(replacement)
    replacement[field] = bad_value
    with pytest.raises(AssertionError):
        verify(legacy, replacement)


def test_demo_keeps_providers_separate_and_no_external_cache() -> None:
    root = Path(__file__).resolve().parents[1]
    runner = (root / "examples/migration/run_demo.py").read_text(
        encoding="utf-8"
    )
    app = (root / "examples/migration/app.py").read_text(
        encoding="utf-8"
    )
    assert "venv.EnvBuilder(with_pip=True)" in runner
    assert '"-I"' in runner
    assert "TemporaryDirectory" in runner
    assert '"fastapi-cache2==0.2.2"' in runner
    assert '"fastapi-cache-stable==0.6.0"' in runner
    assert "redis.Redis" not in app
    assert "Bearer demo-alice" in app

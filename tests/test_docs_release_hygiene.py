"""Keep guides release-agnostic; use the changelog for historic versions."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "guide",
    ["README.md", "MIGRATION.md", "COMPATIBILITY.md", "SUPPORT.md"],
)
def test_user_guides_do_not_pin_old_prerelease_versions(guide: str) -> None:
    contents = (ROOT / guide).read_text(encoding="utf-8")
    assert not re.search(r"\b0\.3\.0(?:a\d+|b\d+|rc\d+)\b", contents)


def test_release_checklist_retains_version_independent_provenance() -> None:
    contents = (ROOT / "docs" / "releases" / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    for artifact in ("Wheel", "Sdist"):
        assert re.search(
            rf"{artifact} SHA-256:\s*`[0-9a-f]{{64}}`", contents
        ), f"missing verified {artifact} hash"
    assert "pypi.org/project/fastapi-cache-stable/" in contents
    assert "Before stable promotion" in contents


def test_release_records_are_archived_outside_root() -> None:
    assert not list(ROOT.glob("RELEASE_*.md"))
    releases = ROOT / "docs" / "releases"
    assert (releases / "RELEASE_NOTES_0.4.0.md").is_file()
    assert (releases / "RELEASE_STATUS_0.4.0.md").is_file()


def test_security_evidence_is_archived_outside_root() -> None:
    evidence = ROOT / "audit" / "security"
    assert (evidence / "SECURITY_ADVISORY_TRIAGE.csv").is_file()
    assert (evidence / "SECURITY_DEPENDENCY_INVENTORY.md").is_file()
    assert (evidence / "DEPENDABOT_ALERTS_2026-11-16.csv").is_file()
    assert not list(ROOT.glob("DEPENDABOT_ALERTS_*.csv"))


def test_redis_example_does_not_expose_working_directory_as_static() -> None:
    # The HTML template has no static assets. Serving "." could expose source
    # and configuration files and activate legacy Starlette FileResponse paths.
    example = (ROOT / "examples" / "redis" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "StaticFiles" not in example
    assert "app.mount(" not in example

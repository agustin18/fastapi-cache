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
    contents = (ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    for artifact in ("Wheel", "Sdist"):
        assert re.search(
            rf"{artifact} SHA-256:\s*`[0-9a-f]{{64}}`", contents
        ), f"missing verified {artifact} hash"
    assert "pypi.org/project/fastapi-cache-stable/" in contents
    assert "Before stable promotion" in contents

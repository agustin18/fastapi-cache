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


def test_release_checklist_retains_exact_published_artifact() -> None:
    contents = (ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "0.3.0rc1" in contents
    assert (
        "251d5249feb319e99ba3438c929b618124a34525a4188dbe3817973d1edba6db"
        in contents
    )
    assert "Before stable promotion" in contents

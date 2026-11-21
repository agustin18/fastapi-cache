"""Keep exact Towncrier promotion verification version-neutral and fail-closed."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exact_release_changelog_gate_is_version_independent() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "towncrier.yml"
    ).read_text(encoding="utf-8")

    # A final promotion must regenerate CHANGELOG from the unmodified base
    # fragment inventory and compare every byte of the checked-in result.
    assert "previous == current" in workflow
    assert "assert previous == current == \"0.5.0\"" not in workflow
    assert "assert f\"## [{current}]\" not in base_changelog" in workflow
    assert "datetime.date.fromisoformat(release_date)" in workflow
    assert "git ls-tree -r --name-only origin/stable changelog.d" in workflow
    assert 'towncrier build --yes --version "$release_version" --date "$release_date"' in workflow
    assert 'diff -u "$worktree/CHANGELOG.md" "$GITHUB_WORKSPACE/CHANGELOG.md"' in workflow
    assert "Unexpected new release fragment in promotion PR" in workflow
    assert "towncrier check --compare-with origin/stable" in workflow


def test_historical_release_headers_remain_archived() -> None:
    # This test must continue passing when the real 0.6.0 CHANGELOG
    # is generated in a later, separately approved promotion PR.
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.5.0]" in changelog
    assert "## [0.4.1]" in changelog

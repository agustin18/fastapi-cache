"""Regression tests for the Towncrier documentation-only gate."""

from scripts.check_changelog_scope import is_docs_only


def test_single_release_status_markdown_is_docs_only() -> None:
    assert is_docs_only(["docs/releases/RELEASE_STATUS_0.4.0.md"])


def test_multiple_documentation_updates_are_docs_only() -> None:
    assert is_docs_only(
        ["README.md", "MIGRATION.md", "docs/QUICKSTART.md", "docs/api/index.rst"]
    )


def test_code_and_docs_requires_changelog() -> None:
    assert not is_docs_only(
        ["fastapi_cache/decorator.py", "docs/releases/RELEASE_STATUS_0.4.0.md"]
    )


def test_workflows_and_tooling_require_changelog() -> None:
    for path in (
        ".github/workflows/ci.yml",
        "scripts/reconcile_dependabot_alerts.py",
        "scripts/check_changelog_scope.py",
        "pyproject.toml",
        "poetry.lock",
        "tests/test_auth_privacy.py",
        "examples/redis/main.py",
    ):
        assert not is_docs_only([path]), path


def test_rename_from_code_to_markdown_does_not_bypass() -> None:
    # The git diff command uses --no-renames; both names are visible.
    assert not is_docs_only(["fastapi_cache/legacy.py", "docs/legacy.md"])


def test_unknown_file_types_fail_closed() -> None:
    assert not is_docs_only(["docs/release-evidence.json"])
    assert not is_docs_only(["docs/example.ipynb"])


def test_no_diff_fails_closed() -> None:
    assert not is_docs_only([])

# Temporary negative gate test comment.

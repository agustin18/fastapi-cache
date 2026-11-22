"""Regression gates for the optional manual GitHub Pages deployment (#48)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "docs-pages.yml"
HOSTING = ROOT / "docs" / "HOSTING_AND_VERSIONING.md"


def test_manual_pages_build_cannot_request_deploy_tokens() -> None:
    data = WORKFLOW.read_text(encoding="utf-8")
    top, jobs = data.split("jobs:\n", 1)
    build, deploy = jobs.split("\n  deploy:\n", 1)
    assert "  workflow_dispatch:" in top
    assert "\n  push:" not in top
    assert "\n  pull_request:" not in top
    assert "permissions: {}" in top
    assert "pages: write" not in build
    assert "id-token: write" not in build
    assert "contents: read" in build
    assert "persist-credentials: false" in build
    assert "if: github.ref == 'refs/heads/stable'" in build
    assert "    needs: build" in deploy
    assert "if: github.ref == 'refs/heads/stable'" in deploy
    assert "pages: write" in deploy
    assert "id-token: write" in deploy
    assert "github-pages" in deploy
    assert "actions/configure-pages@" in deploy
    assert "actions/deploy-pages@" in deploy


def test_environment_branch_protection_is_required_in_manual_runbook() -> None:
    text = HOSTING.read_text(encoding="utf-8")
    assert "Settings → Environments → github-pages" in text
    assert "only `stable`" in text
    assert "environment branch restriction is a security requirement" in text
    assert "workflow that changes its own `if` guard" in text

def test_pages_checks_version_from_package_metadata() -> None:
    data = WORKFLOW.read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "docs-site.yml").read_text(
        encoding="utf-8"
    )
    for source in (data, workflow):
        assert "python scripts/check_docs_version.py --site-dir site" in source
        assert 'if "0.5.0" not in main' not in source
        assert 'assert "0.6.0" in pages' not in source

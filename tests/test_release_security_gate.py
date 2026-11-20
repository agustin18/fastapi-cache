"""Protect the production PyPI security gate from being silently disconnected."""

from pathlib import Path


def test_pypi_requires_authenticated_dependabot_delta() -> None:
    workflow = (
        Path(__file__).resolve().parents[1] / ".github/workflows/publish.yml"
    ).read_text()
    gate = workflow.split("\n  security-delta:\n", 1)[1].split(
        "\n  test:\n", 1
    )[0]
    publish = workflow.split("\n  publish:\n", 1)[1]

    assert "needs: preflight" in gate
    assert "vulnerability-alerts: read" in gate
    assert "GH_TOKEN: ${{ github.token }}" in gate
    assert '--delta --repository "$GITHUB_REPOSITORY"' in gate
    assert "needs: [build, security-delta]" in publish
    assert "environment:" in publish
    assert "name: pypi" in publish

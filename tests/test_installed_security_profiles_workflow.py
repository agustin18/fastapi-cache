"""Guard the independent installed-runtime security-profile workflow."""

from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github/workflows/security-installed-profiles.yml"
)


def test_required_extra_and_sdist_lanes_are_present() -> None:
    workflow = WORKFLOW.read_text()
    for version in ("3.11", "3.12", "3.13", "3.14"):
        for extra in ("none", "redis"):
            assert (
                f'{{python: "{version}", extra: "{extra}", distribution: "wheel"}}'
                in workflow
            )
    for version in ("3.12", "3.14"):
        assert (
            f'{{python: "{version}", extra: "all", distribution: "sdist"}}'
            in workflow
        )


def test_profiles_install_and_audit_real_distribution() -> None:
    workflow = WORKFLOW.read_text()
    assert "python -m build" in workflow
    assert '"$RUNNER_TEMP/consumer/bin/python" -m pip install "$distribution"' in workflow
    assert (
        '"$RUNNER_TEMP/consumer/bin/python" -m pip install '
        '"$distribution[$PROFILE_EXTRA]"'
    ) in workflow
    assert '"$RUNNER_TEMP/consumer/bin/python" -m pip check' in workflow
    assert "setuptools==84.2.1" in workflow
    assert "pip-audit==2.10.1" in workflow
    assert '--path "$target" --aliases off --format json' in workflow
    assert "scripts/validate_security_audit.py" in workflow
    assert "installed-packages.json" in workflow
    assert "installed-METADATA.txt" in workflow
    assert "distributions.sha256" in workflow
    assert "if: always()" in workflow
    assert "retention-days: 90" in workflow


def test_profiles_never_publish_and_run_on_dependency_changes() -> None:
    workflow = WORKFLOW.read_text()
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" in workflow
    assert '"pyproject.toml"' in workflow
    assert '"poetry.lock"' in workflow
    assert '"fastapi_cache/**"' in workflow
    assert "contents: read" in workflow
    assert "id-token: write" not in workflow
    assert "gh-action-pypi-publish" not in workflow

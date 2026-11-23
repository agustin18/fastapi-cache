"""Guard the release-candidate workflow against false phase-B provenance claims."""

from pathlib import Path

from scripts.check_docs_version import published_version
from scripts.release_contract import package_version

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "migration-candidate-phase-b.yml"


def test_phase_b_builds_exact_sha_once_and_checks_candidate_files() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for fragment in (
        "github.event.pull_request.head.sha || github.sha",
        "git rev-parse HEAD",
        "build-exact-artifacts:",
        "migration-and-rollback:",
        "needs: build-exact-artifacts",
        "fastapi_cache_stable-{version}-*.whl",
        "fastapi_cache_stable-{version}.tar.gz",
        "sha256sum --check SHA256SUMS",
        "provenance.json",
        '"published": False',
        "twine check",
        "actions/download-artifact@",
        "actions/upload-artifact@",
    ):
        assert fragment in workflow, fragment
    assert "pypa/gh-action-pypi-publish" not in workflow
    assert '"$GITHUB_EVENT_NAME" = "pull_request"' in workflow
    assert "--allow-development" in workflow
    assert "id-token: write" not in workflow


def test_phase_b_uses_isolated_old_new_consumers_and_scoped_redis() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for py in ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13"):
        assert '"' + py + '"' in workflow
    for item in (
        'format: ["wheel", "sdist"]',
        "image: redis:7.4",
        "fastapi-cache2==0.2.2",
        "redis==4.6.0",
        "MIGRATION_E2E_CONFIRM_ISOLATED_REDIS",
        "MIGRATION_E2E_CANDIDATE_VERSION: ${{ needs.build-exact-artifacts.outputs.version }}",
        "migration_redis_e2e.py\" seed",
        "migration_redis_e2e.py\" candidate",
        "migration_redis_e2e.py\" rollback",
        "pip uninstall -y fastapi-cache-stable",
        "candidate_inmemory_probe.py",
        "redis_vary_probe.py",
        "pip check",
        "cd /tmp",
    ):
        assert item in workflow, item
    assert "FLUSHDB" not in workflow
    assert "flushdb()" not in workflow


def test_candidate_source_metadata_and_published_history() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    support = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")
    notes = (
        ROOT / "docs" / "releases" / "RELEASE_NOTES_0.5.0.md"
    ).read_text(encoding="utf-8")
    checklist = (
        ROOT / "docs" / "releases" / "RELEASE_CANDIDATE_0.5.0.md"
    ).read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    version = package_version(allow_development=True)
    published = published_version()
    assert f'version = "{version}"' in pyproject
    assert f'fastapi-cache-stable[redis]=={published}' in readme
    assert "pypi.org/project/fastapi-cache-stable/" in readme
    assert "0.5.0 is a source candidate, not on PyPI" not in readme
    assert f"**Latest published stable:** [{published}" in readme
    assert "candidate only, not published" not in support
    assert "PREPUBLICATION DRAFT" not in notes
    assert "NOT RELEASED" not in checklist
    assert "71/71" in checklist
    assert "13/13" in checklist
    assert "phase-b" in checklist.lower()
    assert "## [0.5.0]" in changelog
    assert changelog.index("## [0.5.0]") < changelog.index("## [0.4.1]")
    for fragment in (
        "53.feature.md",
        "66.doc.md",
        "66.misc.md",
        "69.doc.md",
        "69.misc.md",
    ):
        assert not (ROOT / "changelog.d" / fragment).exists(), fragment


def test_phase_b_reuses_migration_golden_without_modifying_phase_a() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "migration-published-parity.yml"
    ).read_text(encoding="utf-8")
    assert "fastapi-cache2==0.2.2" in workflow
    assert "fastapi-cache-stable==0.4.1" in workflow
    assert "candidate_050_inmemory_probe.py" not in workflow
    candidate = (ROOT / "tests" / "candidate_inmemory_probe.py").read_text(encoding="utf-8")
    assert "6c5186afe53d101dea5118bda9aebbcf" in candidate
    assert "site-packages" in candidate
    assert 'metadata.version("fastapi-cache-stable") == version' in candidate

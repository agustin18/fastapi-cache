"""Adversarial tests for the immutable release evidence gate."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import pytest
from scripts.verify_release_bundle import WORKFLOW, validate_run, verify_bundle

SHA = "a" * 40
REPO = "agustin18/fastapi-cache"
RUN_ID = "100"
VERSION = "0.6.0"
WHEEL = "fastapi_cache_stable-0.6.0-py3-none-any.whl"
SDIST = "fastapi_cache_stable-0.6.0.tar.gz"
WHEEL_HASH = hashlib.sha256(b"wheel").hexdigest()
SDIST_HASH = hashlib.sha256(b"sdist").hexdigest()


def run_record() -> Dict[str, Any]:
    return {
        "id": 100,
        "head_repository": {"full_name": REPO},
        "head_sha": SHA,
        "head_branch": "stable",
        "event": "workflow_dispatch",
        "path": WORKFLOW,
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
    }


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    (tmp_path / WHEEL).write_bytes(b"wheel")
    (tmp_path / SDIST).write_bytes(b"sdist")
    (tmp_path / "SHA256SUMS").write_text(
        f"{WHEEL_HASH}  {WHEEL}\n{SDIST_HASH}  {SDIST}\n"
    )
    (tmp_path / "provenance.json").write_text(json.dumps({
        "source_sha": SHA,
        "workflow_run_id": RUN_ID,
        "workflow_attempt": "1",
        "candidate_version": VERSION,
        "wheel": WHEEL,
        "sdist": SDIST,
        "published": False,
    }))
    return tmp_path


def test_exact_bundle_is_accepted(bundle: Path) -> None:
    run = run_record()
    validate_run(run, REPO, SHA, RUN_ID)
    assert verify_bundle(bundle, run, SHA, VERSION, WHEEL_HASH, SDIST_HASH) == {
        WHEEL: WHEEL_HASH,
        SDIST: SDIST_HASH,
    }


@pytest.mark.parametrize(("field", "value", "message"), [
    ("id", 101, "unexpected workflow run id"),
    ("head_repository", {"full_name": "other/repo"}, "belong to this repository"),
    ("head_sha", "b" * 40, "run source SHA mismatch"),
    ("head_branch", "feature", "run must be on stable"),
    ("event", "pull_request", "manual final run required"),
    ("path", ".github/workflows/other.yml", "wrong evidence workflow"),
    ("status", "in_progress", "evidence run is incomplete"),
    ("conclusion", "failure", "evidence run did not pass"),
])
def test_unapproved_runs_are_rejected(field: str, value: Any, message: str) -> None:
    run = run_record()
    run[field] = value
    with pytest.raises(ValueError, match=message):
        validate_run(run, REPO, SHA, RUN_ID)


@pytest.mark.parametrize(("field", "value", "message"), [
    ("source_sha", "b" * 40, "bundle source SHA mismatch"),
    ("workflow_run_id", "101", "bundle run mismatch"),
    ("workflow_attempt", "2", "bundle attempt mismatch"),
    ("candidate_version", "0.5.0", "bundle version mismatch"),
    ("published", True, "expected unpublished evidence bundle"),
    ("wheel", "../wrong.whl", "unexpected wheel name"),
    ("sdist", "other.tar.gz", "unexpected sdist name"),
])
def test_unapproved_provenance_is_rejected(
    bundle: Path, field: str, value: Any, message: str
) -> None:
    path = bundle / "provenance.json"
    metadata = json.loads(path.read_text())
    metadata[field] = value
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match=message):
        verify_bundle(bundle, run_record(), SHA, VERSION, WHEEL_HASH, SDIST_HASH)


@pytest.mark.parametrize("filename", [WHEEL, SDIST])
def test_mutated_distribution_is_rejected(bundle: Path, filename: str) -> None:
    (bundle / filename).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        verify_bundle(bundle, run_record(), SHA, VERSION, WHEEL_HASH, SDIST_HASH)


def test_extra_file_and_manifest_mismatch_rejected(bundle: Path) -> None:
    extra = bundle / "unexpected"
    extra.write_text("unexpected")
    with pytest.raises(ValueError, match="contents"):
        verify_bundle(bundle, run_record(), SHA, VERSION, WHEEL_HASH, SDIST_HASH)
    extra.unlink()
    (bundle / "SHA256SUMS").write_text("wrong")
    with pytest.raises(ValueError, match="manifest"):
        verify_bundle(bundle, run_record(), SHA, VERSION, WHEEL_HASH, SDIST_HASH)


def test_publish_workflows_use_same_approved_artifact_pair() -> None:
    workflows = Path(__file__).resolve().parents[1] / ".github" / "workflows"
    for name in ("publish.yml", "publish-testpypi.yml"):
        source = (workflows / name).read_text()
        assert "evidence_run_id:" in source
        assert "wheel_sha256:" in source
        assert "sdist_sha256:" in source
        assert "python -m build" not in source
        assert "scripts/verify_release_bundle.py" in source
        assert "sha256sum --check" in source
        assert 'test "$GITHUB_REF" = "refs/tags/v$version"' in source
    assert "--require-testpypi" in (workflows / "publish.yml").read_text()
    phase_b = (workflows / "migration-candidate-phase-b.yml").read_text()
    assert "exact-installed-security:" in phase_b
    assert "uses: ./.github/workflows/security-installed-profiles.yml" in phase_b
    assert "artifact_name: migration-phase-b-060-distributions" in phase_b

"""Adversarial tests for the immutable release evidence gate."""

import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import pytest
from scripts import verify_release_bundle
from scripts.release_contract import (
    BUILD_JOB,
    artifact_name,
    package_version,
    validate_version,
)
from scripts.verify_release_bundle import (
    WORKFLOW,
    validate_jobs,
    validate_run,
    verify_bundle,
    verify_test_index,
)

SHA = "a" * 40
REPO = "agustin18/fastapi-cache"
RUN_ID = "100"
VERSION = "0.7.0"  # Dry-run the NEXT release with synthetic local evidence.
WHEEL = f"fastapi_cache_stable-{VERSION}-py3-none-any.whl"
SDIST = f"fastapi_cache_stable-{VERSION}.tar.gz"
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
        "artifact_name": artifact_name(VERSION),
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
    ("run_attempt", 2, "new manual dispatch required"),
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
    ("artifact_name", "migration-phase-b-0.6.0-distributions", "unexpected evidence artifact name"),
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
        assert "python -m scripts.verify_release_bundle" in source
        assert "sha256sum --check" in source
        assert 'test "$GITHUB_REF" = "refs/tags/v$version"' in source
    assert "--require-testpypi" in (workflows / "publish.yml").read_text()
    phase_b = (workflows / "migration-candidate-phase-b.yml").read_text()
    assert "exact-installed-security:" in phase_b
    assert "uses: ./.github/workflows/security-installed-profiles.yml" in phase_b
    assert "artifact_name: ${{ needs.build-exact-artifacts.outputs.artifact_name }}" in phase_b


def job_record() -> Dict[str, Any]:
    names = [BUILD_JOB]
    names.extend(
        f"Py {version} / {kind} / real Redis 7.4 / rollback"
        for version in ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13")
        for kind in ("wheel", "sdist")
    )
    names.extend(
        f"Exact artifact security / Python {version} / {extra} / wheel"
        for version in ("3.11", "3.12", "3.13")
        for extra in ("none", "redis")
    )
    names.append("Exact artifact security / Python 3.12 / all / sdist")
    return {
        "total_count": 20,
        "jobs": [
            {"name": name, "run_id": 100, "status": "completed", "conclusion": "success"}
            for name in names
        ],
    }


def test_complete_first_attempt_jobs() -> None:
    validate_jobs(job_record(), RUN_ID)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "wrong_run", "failure", "skipped", "incomplete"])
def test_reject_unapproved_jobs(mutation: str) -> None:
    payload = job_record()
    jobs = payload["jobs"]
    if mutation == "missing":
        jobs.pop()
    elif mutation == "extra":
        jobs.append(dict(jobs[0], name="unexpected"))
    elif mutation == "duplicate":
        jobs[-1]["name"] = jobs[0]["name"]
    elif mutation == "wrong_run":
        jobs[-1]["run_id"] = 101
    elif mutation == "incomplete":
        jobs[-1]["status"] = "in_progress"
    else:
        jobs[-1]["conclusion"] = mutation
    with pytest.raises(ValueError, match="Phase B job"):
        validate_jobs(payload, RUN_ID)


def index_payload() -> Dict[str, Any]:
    return {
        "info": {"version": VERSION},
        "urls": [
            {"filename": name, "digests": {"sha256": digest}, "yanked": False}
            for name, digest in ((WHEEL, WHEEL_HASH), (SDIST, SDIST_HASH))
        ],
    }


@pytest.mark.parametrize("mutation", ["exact", "wrong_hash", "missing", "extra", "duplicate", "wrong_version", "yanked"])
def test_testpypi_exact_pair(monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    payload = index_payload()
    files = payload["urls"]
    if mutation == "wrong_hash":
        files[0]["digests"]["sha256"] = "0" * 64
    elif mutation == "missing":
        files.pop()
    elif mutation == "extra":
        files.append(dict(files[0], filename="unexpected.whl"))
    elif mutation == "duplicate":
        files[1] = files[0]
    elif mutation == "wrong_version":
        payload["info"]["version"] = "0.5.0"
    elif mutation == "yanked":
        files[0]["yanked"] = True

    def fake_open(url: str, timeout: int) -> BytesIO:
        assert url == f"https://test.pypi.org/pypi/fastapi-cache-stable/{VERSION}/json"
        assert timeout == 30
        return BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(verify_release_bundle, "urlopen", fake_open)
    expected = {WHEEL: WHEEL_HASH, SDIST: SDIST_HASH}
    if mutation == "exact":
        verify_test_index(VERSION, expected)
    else:
        with pytest.raises(ValueError, match="TestPyPI"):
            verify_test_index(VERSION, expected)


def test_testpypi_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        verify_release_bundle, "urlopen", lambda *args, **kwargs: BytesIO(b"not json")
    )
    with pytest.raises(json.JSONDecodeError):
        verify_test_index(VERSION, {WHEEL: WHEEL_HASH, SDIST: SDIST_HASH})


def test_testpypi_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*args: Any, **kwargs: Any) -> None:
        raise OSError("unreachable")

    monkeypatch.setattr(verify_release_bundle, "urlopen", unavailable)
    with pytest.raises(OSError, match="unreachable"):
        verify_test_index(VERSION, {WHEEL: WHEEL_HASH, SDIST: SDIST_HASH})

def test_future_version_agnostic_release_contract(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "fastapi-cache-stable"\nversion = "0.7.0"\n',
        encoding="utf-8",
    )
    assert package_version(pyproject) == VERSION
    dev_source = tmp_path / "development.toml"
    dev_source.write_text(
        '[tool.poetry]\nname = "fastapi-cache-stable"\nversion = "0.7.0.dev0"\n',
        encoding="utf-8",
    )
    assert package_version(dev_source, allow_development=True) == "0.7.0.dev0"
    assert artifact_name("0.7.0.dev0", allow_development=True) == "migration-phase-b-0.7.0.dev0-distributions"
    with pytest.raises(ValueError, match="final"):
        package_version(dev_source)
    with pytest.raises(ValueError, match="final"):
        artifact_name("0.7.0.dev0")
    assert artifact_name(VERSION) == "migration-phase-b-0.7.0-distributions"
    for wrong in ("0.7.0rc1", "0.7", "../0.7.0", "0.7.0;echo unexpected"):
        with pytest.raises(ValueError, match="final X.Y.Z"):
            validate_version(wrong)


def test_wrong_distribution_name_fails_closed(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.poetry]\nname = "other"\nversion = "0.7.0"\n')
    with pytest.raises(ValueError, match="distribution name"):
        package_version(pyproject)


def test_publish_workflows_no_longer_pin_a_past_artifact() -> None:
    workflows = Path(__file__).resolve().parents[1] / ".github" / "workflows"
    for name in ("publish.yml", "publish-testpypi.yml"):
        content = (workflows / name).read_text(encoding="utf-8")
        assert "migration-phase-b-060-distributions" not in content
        assert "python scripts/release_contract.py artifact" in content
    workflow = (workflows / "migration-candidate-phase-b.yml").read_text()
    assert "migration-phase-b-060-distributions" not in workflow
    assert "fastapi_cache_stable-0.6.0-" not in workflow
    assert 'candidate_version": "0.6.0"' not in workflow

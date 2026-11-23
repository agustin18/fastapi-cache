"""Network-free tests for the local exact-candidate wheel gate."""

import hashlib
import zipfile
from pathlib import Path

import pytest
from benchmarks.candidate_artifact import verify_candidate_wheel


def _wheel(tmp_path: Path, version: str = "0.7.0.dev0", *,
           package: str = "fastapi-cache-stable",
           metadata_version: str = "0.7.0.dev0") -> Path:
    wheel = tmp_path / f"fastapi_cache_stable-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, mode="w") as archive:
        archive.writestr(
            f"fastapi_cache_stable-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.3\nName: {package}\nVersion: {metadata_version}\n",
        )
        archive.writestr("fastapi_cache/__init__.py", "pass\n")
    return wheel


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_dev_candidate_wheel_metadata_and_hash_verified(tmp_path: Path) -> None:
    wheel = _wheel(tmp_path)
    assert verify_candidate_wheel(wheel, "0.7.0.dev0", _hash(wheel)) == _hash(wheel)


def test_final_candidate_identity_is_allowed_but_not_published(tmp_path: Path) -> None:
    wheel = _wheel(tmp_path, "0.7.0", metadata_version="0.7.0")
    assert verify_candidate_wheel(wheel, "0.7.0", _hash(wheel)) == _hash(wheel)


def test_modified_wheel_cannot_reuse_approved_digest(tmp_path: Path) -> None:
    wheel = _wheel(tmp_path)
    original = _hash(wheel)
    with zipfile.ZipFile(wheel, mode="a") as archive:
        archive.writestr("other.txt", "tampered")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_candidate_wheel(wheel, "0.7.0.dev0", original)


@pytest.mark.parametrize(
    ("version", "digest", "message"),
    [
        ("0.7.0rc1", "a" * 64, "version"),
        ("../0.7.0", "a" * 64, "version"),
        ("0.7.0.dev0", "abcd", "SHA-256"),
        ("0.7.0", "a" * 64, "filename"),
    ],
)
def test_invalid_candidate_identity_fails_closed(
    tmp_path: Path, version: str, digest: str, message: str
) -> None:
    wheel = _wheel(tmp_path)
    with pytest.raises(ValueError, match=message):
        verify_candidate_wheel(wheel, version, digest)


def test_wrong_candidate_distribution_and_metadata_rejected(tmp_path: Path) -> None:
    for override in ({"package": "fastapi-cache2"}, {"metadata_version": "0.6.0"}):
        wheel = _wheel(tmp_path, **override)
        with pytest.raises(ValueError, match="identity|version"):
            verify_candidate_wheel(wheel, "0.7.0.dev0", _hash(wheel))


def test_published_baseline_must_use_published_hash_path(tmp_path: Path) -> None:
    wheel = _wheel(tmp_path, "0.6.0", metadata_version="0.6.0")
    with pytest.raises(ValueError, match="immutable published"):
        verify_candidate_wheel(wheel, "0.6.0", _hash(wheel))

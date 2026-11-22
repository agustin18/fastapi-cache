"""Version gates derive active docs from the package metadata, not CI literals."""
from pathlib import Path

import pytest
from scripts.check_docs_version import published_version, validate

ROOT = Path(__file__).resolve().parents[1]


def test_package_is_single_current_version_source() -> None:
    assert published_version().count(".") == 2
    assert published_version() in (ROOT / "README.md").read_text(encoding="utf-8")


def test_missing_current_version_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "pyproject.toml"
    project.write_text('[tool.poetry]\nname = "example"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Missing final"):
        published_version(project)


def test_current_docs_metadata_cannot_drift(tmp_path: Path) -> None:
    # A site without verified, version-correct HTML is never deployable.
    (tmp_path / "index.html").write_text("CURRENT RELEASE 0.5.0")
    with pytest.raises(ValueError, match="not aligned"):
        validate(tmp_path, ROOT)

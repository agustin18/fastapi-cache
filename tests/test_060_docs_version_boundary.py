"""Keep the published 0.6.0 metadata and installation boundaries accurate."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_and_quickstart_expose_published_060() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/QUICKSTART.md")
    assert "Latest published stable:** [0.6.0" in readme
    assert 'fastapi-cache-stable[redis]==0.6.0' in readme
    assert 'fastapi-cache-stable==0.6.0' in quickstart
    assert "0.6.0 release" in quickstart
    assert "max_entries" in readme
    assert "AttributeError" in readme


def test_changelog_and_release_status_are_version_ordered() -> None:
    changelog = _read("CHANGELOG.md")
    status = _read("docs/releases/RELEASE_STATUS_0.6.0.md")
    assert "## [0.6.0]" in changelog
    assert changelog.index("## [0.6.0]") < changelog.index("## [0.5.0]")
    assert "0.6.0" in status
    assert "0.5.0" in status


def test_no_prepublication_install_pin_remains() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/QUICKSTART.md")
    assert 'fastapi-cache-stable[redis]==0.5.0' not in readme
    assert 'fastapi-cache-stable==0.5.0' not in quickstart
    assert "not yet published" not in readme.lower()

"""Published-docs checks remain fixed while source metadata can advance."""
from pathlib import Path

import pytest
from packaging.version import Version
from scripts.check_docs_version import published_version, validate
from scripts.release_contract import package_version

ROOT = Path(__file__).resolve().parents[1]


def source_may_advance(source: str, published: str) -> bool:
    """Source metadata may move ahead while public docs keep the published pin."""
    return Version(source) >= Version(published)


def test_published_docs_identity_is_separate_from_development_source() -> None:
    published = published_version()
    source = package_version(allow_development=True)
    assert published.count(".") == 2
    assert source_may_advance(source, published)
    assert published in (ROOT / "README.md").read_text(encoding="utf-8")
    assert published in (ROOT / f"docs/releases/RELEASE_STATUS_{published}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("source", "published", "allowed"),
    [
        ("0.8.0", "0.7.2", True),
        ("0.8.0.dev0", "0.7.2", True),
        ("0.7.2", "0.7.2", True),
        ("0.7.1", "0.7.2", False),
        ("0.6.9", "0.7.2", False),
    ],
)
def test_source_version_policy_allows_forward_progress_only(
    source: str, published: str, allowed: bool
) -> None:
    assert source_may_advance(source, published) is allowed


def test_missing_current_version_fails_closed(tmp_path: Path) -> None:
    marker = tmp_path / "PUBLISHED_VERSION"
    marker.write_text("0.7.0.dev0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing final"):
        published_version(marker)
    marker.write_text("0.6.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing release status"):
        published_version(marker)


def test_current_docs_metadata_cannot_drift(tmp_path: Path) -> None:
    # A site without verified, version-correct HTML is never deployable.
    (tmp_path / "index.html").write_text("CURRENT RELEASE 0.5.0")
    with pytest.raises(ValueError, match="not aligned"):
        validate(tmp_path, ROOT)



@pytest.mark.parametrize(
    "filename",
    [
        "site_docs/reference/api.md",
        "site_docs/reference/alternatives.md",
        "site_docs/backends.md",
        "site_docs/reference/compatibility.md",
    ],
)
def test_public_reference_markers_cannot_revert_to_old_release(
    tmp_path: Path, filename: str
) -> None:
    """A source page stale by one release must fail before HTML inspection."""
    files = [
        "README.md",
        "docs/QUICKSTART.md",
        "site_docs/index.md",
        "site_docs/roadmap.md",
        "site_docs/reference/features.md",
        "docs/DOCS_SITE.md",
        "docs/releases/README.md",
        "site_docs/reference/api.md",
        "site_docs/reference/alternatives.md",
        "site_docs/backends.md",
        "site_docs/reference/compatibility.md",
    ]
    (tmp_path / "pyproject.toml").write_text(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    version = published_version()
    for name in (
        "docs/releases/PUBLISHED_VERSION",
        f"docs/releases/RELEASE_STATUS_{version}.md",
    ):
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
    version = published_version()
    for name in files:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = (ROOT / name).read_text(encoding="utf-8")
        if name == filename:
            source = source.replace(version, "0.0.0")
        destination.write_text(source, encoding="utf-8")

    with pytest.raises(ValueError, match="not aligned") as exc:
        validate(tmp_path, tmp_path)
    assert str(exc.value).startswith(filename + " is not aligned")


@pytest.mark.parametrize(
    ("filename", "current_marker", "stale_marker"),
    [
        (
            "site_docs/guides/redis.md",
            'fastapi-cache-stable[redis]=={version}',
            'fastapi-cache-stable[redis]==0.6.0',
        ),
        (
            "site_docs/guides/redis.md",
            "redis-py versions allowed in {version} metadata",
            "redis-py versions allowed in 0.6.0 metadata",
        ),
        (
            "site_docs/guides/troubleshooting.md",
            "{version} declares `>=3.8,<3.15`",
            "0.6.0 declares `>=3.8,<3.14`",
        ),
    ],
)
def test_stale_redis_and_troubleshooting_claims_are_rejected(
    tmp_path: Path, filename: str, current_marker: str, stale_marker: str
) -> None:
    """Keep both the Redis pin and capability table aligned with the release."""
    files = [
        "README.md",
        "docs/QUICKSTART.md",
        "site_docs/index.md",
        "site_docs/roadmap.md",
        "site_docs/reference/api.md",
        "site_docs/reference/alternatives.md",
        "site_docs/backends.md",
        "site_docs/reference/compatibility.md",
        "site_docs/reference/features.md",
        "site_docs/guides/redis.md",
        "site_docs/guides/troubleshooting.md",
        "docs/DOCS_SITE.md",
        "docs/releases/README.md",
    ]
    (tmp_path / "pyproject.toml").write_text(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    version = published_version()
    for name in (
        "docs/releases/PUBLISHED_VERSION",
        f"docs/releases/RELEASE_STATUS_{version}.md",
    ):
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
    version = published_version()
    current_marker = current_marker.format(version=version)
    for name in files:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / name).read_text(encoding="utf-8")
        if name == filename:
            assert text.count(current_marker) == 1
            text = text.replace(current_marker, stale_marker)
        target.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="not aligned") as exc:
        validate(tmp_path, tmp_path)
    assert str(exc.value).startswith(filename + " is not aligned")

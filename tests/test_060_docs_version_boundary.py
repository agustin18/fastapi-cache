"""Prevent source-only #85 API from being marketed as published 0.5.0."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_published_050_inmemory_remains_documented_as_unbounded() -> None:
    guide = _read("site_docs/guides/inmemory.md")
    api = _read("site_docs/reference/api.md")
    quickstart = _read("docs/QUICKSTART.md")
    assert "Published 0.5.0 has **no `max_entries` constructor argument**" in guide
    assert "unbounded in published 0.5.0" in api
    assert "Published 0.5.0 InMemory is **unbounded per process**" in quickstart


def test_merged_source_api_is_labelled_unreleased() -> None:
    guide = _read("site_docs/guides/inmemory.md")
    api = _read("site_docs/reference/api.md")
    matrix = _read("site_docs/reference/features.md")
    releases = _read("site_docs/reference/releases.md")
    assert "InMemoryBackend(max_entries=1_000)" in guide
    assert "read-only" in guide
    assert "AttributeError" in guide
    assert "not supported by 0.5.0" in guide
    assert "max_entries: Optional[int]" in api
    assert "not part of a published 0.6.0 distribution" in api
    assert "Merged source, unreleased" in matrix
    assert "not in published 0.5.0" in matrix
    assert "not part of any published 0.5.0 artifact" in releases


def test_readme_and_roadmap_do_not_claim_060_was_published() -> None:
    readme = _read("README.md")
    roadmap = _read("ROADMAP.md")
    assert "not available with the 0.5.0 install pin" in readme
    assert "read-only" in readme
    assert "AttributeError" in readme
    assert "not available in the immutable published 0.5.0 wheel" in roadmap.lower()
    assert "#50" in roadmap
    assert "0.7.0" in roadmap
    assert "190d105915972d436ddbf4ad152ad654a4db392a" in roadmap

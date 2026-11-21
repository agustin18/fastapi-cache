"""Fail-closed checks for built-site relative links and page fragments."""

from pathlib import Path

from scripts.check_docs_links import check_site


def _page(root: Path, path: str, html: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def test_links_check_every_html_and_anchors(tmp_path: Path) -> None:
    _page(
        tmp_path,
        "index.html",
        '<html><a href="start/">Start</a><a href="/start/#ready">Anchor</a>'
        '<a href="https://example.org">External</a></html>',
    )
    _page(tmp_path, "start/index.html", '<html><h2 id="ready">Ready</h2></html>')
    pages, links, errors = check_site(tmp_path)
    assert pages == 2
    assert links == 2
    assert errors == []


def test_links_detect_broken_relative_file_and_fragment(tmp_path: Path) -> None:
    _page(
        tmp_path,
        "index.html",
        '<html><a href="missing/">Missing</a><a href="start/#typo">Typo</a></html>',
    )
    _page(tmp_path, "start/index.html", '<html><h2 id="ready">Ready</h2></html>')
    _, _, errors = check_site(tmp_path)
    assert len(errors) == 2
    assert "missing/" in errors[0]
    assert "missing fragment" in errors[1]


def test_links_block_escape_and_allow_static_assets(tmp_path: Path) -> None:
    _page(
        tmp_path,
        "nested/index.html",
        '<html><a href="../../secret.html">Escape</a>'
        '<a href="../assets/site.css">Asset</a></html>',
    )
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/site.css").write_text("body {}")
    _, _, errors = check_site(tmp_path)
    assert len(errors) == 1
    assert "escapes site" in errors[0]


def test_missing_site_fails(tmp_path: Path) -> None:
    pages, _, errors = check_site(tmp_path)
    assert pages == 0
    assert "No HTML pages" in errors[0]


def test_links_under_github_pages_project_prefix(tmp_path: Path) -> None:
    _page(
        tmp_path,
        "index.html",
        '<html><a href="/fastapi-cache/guide/#ready">Guide</a>'
        '<a href="/fastapi-cache/assets/site.css">Styles</a></html>',
    )
    _page(tmp_path, "guide/index.html", '<html><h2 id="ready">Ready</h2></html>')
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/site.css").write_text("body {}")
    pages, links, errors = check_site(tmp_path, base_path="/fastapi-cache")
    assert pages == 2
    assert links == 2
    assert errors == []


def test_links_deny_absolute_path_outside_pages_base(tmp_path: Path) -> None:
    _page(tmp_path, "index.html", '<html><a href="/other-project/">Wrong</a></html>')
    _, _, errors = check_site(tmp_path, base_path="/fastapi-cache")
    assert len(errors) == 1
    assert "escapes site" in errors[0]

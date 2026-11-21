"""Offline link integrity check for every page in the built documentation site.

Validates built-site-relative links and HTML fragment targets without making
network calls. External links are deliberately out of scope (network-dependent).
"""

import argparse
import posixpath
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs) -> None:
        self._collect(attrs)

    def handle_startendtag(self, tag, attrs) -> None:
        self._collect(attrs)

    def _collect(self, attrs) -> None:
        for name, value in attrs:
            if value is None:
                continue
            if name in {"id", "name"}:
                self.ids.add(value)
            elif name == "href":
                self.links.append(value)


def _target(source: Path, href: str, site: Path):
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or href.startswith("//"):
        return None
    path = unquote(parts.path)
    rel = source.relative_to(site).as_posix()
    if path.startswith("/"):
        target_path = path.lstrip("/")
    elif path:
        target_path = posixpath.join(posixpath.dirname(rel), path)
    else:
        target_path = rel
    normalized = posixpath.normpath(target_path)
    if normalized == ".." or normalized.startswith("../"):
        return ("INVALID", parts.fragment)
    location = site / normalized
    if path.endswith("/") or not location.suffix:
        location = location / "index.html"
    elif location.is_dir():
        location = location / "index.html"
    return (location, unquote(parts.fragment))


def check_site(site: Path) -> tuple:
    site = site.resolve()
    pages = sorted(site.rglob("*.html"))
    if not pages:
        return (0, 0, ["No HTML pages found in " + str(site)])
    parsed = {}
    for source in pages:
        doc = LinkParser()
        doc.feed(source.read_text(encoding="utf-8"))
        parsed[source.resolve()] = doc

    problems = []
    checked = 0
    for source, doc in parsed.items():
        for href in doc.links:
            if not href.strip():
                continue
            result = _target(source, href, site)
            if result is None:
                continue
            checked += 1
            target, fragment = result
            if target == "INVALID":
                problems.append(f"{source.relative_to(site)}: escapes site: {href}")
                continue
            if not target.is_file():
                problems.append(f"{source.relative_to(site)}: missing {href} -> {target}")
                continue
            if fragment and target.suffix.lower() == ".html":
                if target not in parsed:
                    problems.append(f"{source.relative_to(site)}: HTML not parsed {href}")
                elif fragment not in parsed[target].ids:
                    problems.append(f"{source.relative_to(site)}: missing fragment {href}")
    return (len(pages), checked, problems)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    args = parser.parse_args()
    pages, links, errors = check_site(args.site_dir)
    print(f"Documentation: {pages} pages, {links} local links verified")
    if errors:
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(f"{len(errors)} documentation link errors")


if __name__ == "__main__":
    main()

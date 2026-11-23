"""Check public release docs against the last verified published version marker.

Run against built Zensical HTML. Historical release notes, archived guides
and changelogs intentionally retain their original version numbers.
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def published_version(marker=None):
    # This marker changes only after a verified public registry promotion.
    # In development pyproject.toml intentionally names the next dev wheel.
    marker = ROOT / "docs/releases/PUBLISHED_VERSION" if marker is None else Path(marker)
    version = marker.read_text(encoding="utf-8").strip()
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise ValueError("Missing final published version in PUBLISHED_VERSION")
    if not (marker.parent / ("RELEASE_STATUS_" + version + ".md")).is_file():
        raise ValueError("Missing release status evidence for published " + version)
    return version


def validate(site, root=ROOT):
    version = published_version(root / "docs/releases/PUBLISHED_VERSION")
    sources = {
        "README.md": "**Latest published stable:** [" + version,
        "docs/QUICKSTART.md": "fastapi-cache-stable==" + version,
        "site_docs/index.md": "CURRENT RELEASE " + version,
        "site_docs/roadmap.md": "**" + version + " is published.**",
        "site_docs/reference/api.md": "# Public API reference · published " + version,
        "site_docs/reference/alternatives.md": "**fastapi-cache-stable " + version + " is published**",
        "site_docs/backends.md": "| Published " + version + " entry-count bound",
        "site_docs/reference/compatibility.md": "| Item | Published " + version + " |",
        "site_docs/guides/redis.md": (
            "fastapi-cache-stable[redis]==" + version,
            "redis-py versions allowed in " + version + " metadata",
        ),
        "site_docs/guides/troubleshooting.md": version + " declares `>=3.8,<3.14`",
        "site_docs/reference/features.md": "# What ships in " + version + "?",
        "docs/DOCS_SITE.md": "published package remains **fastapi-cache-stable " + version + "**",
        "docs/releases/README.md": "[" + version + " published release notes]",
    }
    for path, expected in sources.items():
        content = (root / path).read_text(encoding="utf-8")
        needles = (expected,) if isinstance(expected, str) else expected
        if any(needle not in content for needle in needles):
            raise ValueError(path + " is not aligned with " + version)

    # The published Redis installation example must contain exactly one
    # versioned package pin; a second stale pin must not silently pass.
    redis_guide = (root / "site_docs/guides/redis.md").read_text(encoding="utf-8")
    redis_pins = re.findall(
        r"fastapi-cache-stable\[redis\]==(\d+\.\d+\.\d+)", redis_guide
    )
    if redis_pins != [version]:
        raise ValueError("site_docs/guides/redis.md is not aligned with " + version)
    # Do not let the release archive claim the *current* published version
    # is still a candidate. Historic checklists keep their original wording.
    archive = (root / "docs/releases/README.md").read_text(encoding="utf-8")
    for line in archive.splitlines():
        if line.startswith("- [" + version) and any(
            phrase in line for phrase in ("NOT RELEASED", "pending final acceptance", "candidate evidence only")
        ):
            raise ValueError("Release archive still marks " + version + " as unpublished")
    for path, needle in (
        ("index.html", "CURRENT RELEASE " + version),
        ("reference/features/index.html", "What ships in " + version),
        ("getting-started/index.html", "fastapi-cache-stable==" + version),
    ):
        output = Path(site) / path
        if not output.is_file() or needle not in output.read_text(encoding="utf-8"):
            raise ValueError(str(output) + " is not aligned with " + version)
    return version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, required=True)
    args = parser.parse_args()
    print("Current docs version verified:", validate(args.site_dir))


if __name__ == "__main__":
    main()

"""Check user-visible current release docs from the single package version source.

Run against built Zensical HTML. Historical release notes, archived guides
and changelogs intentionally retain their original version numbers.
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def published_version(project=None):
    project = ROOT / "pyproject.toml" if project is None else Path(project)
    content = project.read_text(encoding="utf-8")
    part = content.split("[tool.poetry]\n", 1)[1].split("\n[", 1)[0]
    match = re.search(r'(?m)^version\s*=\s*"(\d+\.\d+\.\d+)"\s*$', part)
    if match is None:
        raise ValueError("Missing final package release version in pyproject.toml")
    return match.group(1)


def validate(site, root=ROOT):
    version = published_version(root / "pyproject.toml")
    sources = {
        "README.md": "**Latest published stable:** [" + version,
        "docs/QUICKSTART.md": "fastapi-cache-stable==" + version,
        "site_docs/index.md": "CURRENT RELEASE " + version,
        "site_docs/roadmap.md": "**" + version + " is published.**",
        "site_docs/reference/api.md": "# Public API reference · published " + version,
        "site_docs/reference/alternatives.md": "**fastapi-cache-stable " + version + " is published**",
        "site_docs/backends.md": "| Published " + version + " entry-count bound",
        "site_docs/reference/compatibility.md": "| Item | Published " + version + " |",
        "site_docs/reference/features.md": "# What ships in " + version + "?",
        "docs/DOCS_SITE.md": "published package remains **fastapi-cache-stable " + version + "**",
        "docs/releases/README.md": "[" + version + " published release notes]",
    }
    for path, needle in sources.items():
        if needle not in (root / path).read_text(encoding="utf-8"):
            raise ValueError(path + " is not aligned with " + version)
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

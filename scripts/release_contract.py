"""Shared, version-neutral metadata and artifact identity for future releases.

No tag creation, network access, indexing or publication lives here.
The version is the release-intended value in pyproject.toml. Python 3.8
compatibility is deliberate: the module is imported by legacy CI tests.
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_JOB = "Build exact release wheel + sdist once, record hashes"


def validate_version(version):
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise ValueError("expected a final X.Y.Z release version")
    return version


def package_version(path=None):
    file = ROOT / "pyproject.toml" if path is None else Path(path)
    source = file.read_text(encoding="utf-8")
    try:
        section = source.split("[tool.poetry]\n", 1)[1].split("\n[", 1)[0]
    except IndexError as exc:
        raise ValueError("missing [tool.poetry] metadata") from exc
    package = re.search(r'(?m)^name\s*=\s*"([^"]+)"\s*$', section)
    version = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', section)
    if package is None or package.group(1) != "fastapi-cache-stable":
        raise ValueError("unexpected distribution name")
    if version is None:
        raise ValueError("missing package version")
    return validate_version(version.group(1))


def artifact_name(version):
    return "migration-phase-b-" + validate_version(version) + "-distributions"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("version", "artifact", "github-output"))
    parser.add_argument("--pyproject", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    version = package_version(args.pyproject)
    if args.command == "version":
        print(version)
    elif args.command == "artifact":
        print(artifact_name(version))
    else:
        if args.github_output is None:
            parser.error("--github-output is required")
        with args.github_output.open("a", encoding="utf-8") as target:
            target.write("version=" + version + "\n")
            target.write("artifact_name=" + artifact_name(version) + "\n")


if __name__ == "__main__":
    main()

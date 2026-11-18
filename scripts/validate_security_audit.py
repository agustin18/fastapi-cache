"""Fail closed unless pip-audit covers the entire installed wheel profile."""

from __future__ import annotations

import argparse
import json
import re
from email.parser import Parser
from pathlib import Path
from typing import Any, Mapping

PROJECT_PACKAGE = "fastapi-cache-stable"
UNPUBLISHED_PROJECT_SKIP = "Dependency not found on PyPI and could not be audited: "
_VALID_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z")


def _normalize_name(name: Any) -> str:
    if not isinstance(name, str) or not _VALID_NAME.fullmatch(name):
        raise ValueError(f"invalid package name: {name!r}")
    return re.sub(r"[-_.]+", "-", name).lower()


def _installed_versions(installed_packages: Any) -> dict[str, str]:
    if not isinstance(installed_packages, list) or not installed_packages:
        raise ValueError("installed package inventory is empty or not a list")
    installed: dict[str, str] = {}
    for record in installed_packages:
        if not isinstance(record, Mapping):
            raise ValueError("installed package entry is not an object")
        name = _normalize_name(record.get("name"))
        version = record.get("version")
        if not isinstance(version, str) or not version or version.strip() != version:
            raise ValueError(f"installed package has invalid version: {name}")
        if name in installed:
            raise ValueError(f"duplicate installed package: {name}")
        installed[name] = version
    return installed


def _project_identity(wheel_metadata: str) -> tuple[str, str]:
    message = Parser().parsestr(wheel_metadata, headersonly=True)
    names = message.get_all("Name", [])
    versions = message.get_all("Version", [])
    if len(names) != 1 or len(versions) != 1:
        raise ValueError("wheel metadata requires exactly one Name and Version")
    name = _normalize_name(names[0])
    version = versions[0]
    if name != PROJECT_PACKAGE or not version or version.strip() != version:
        raise ValueError("unexpected project wheel name or version")
    return name, version


def validate_audit_report(
    report: Mapping[str, Any],
    installed_packages: Any,
    wheel_metadata: str,
) -> dict[str, Any]:
    """Require one correct audit record for every installed distribution."""
    installed = _installed_versions(installed_packages)
    project_name, project_version = _project_identity(wheel_metadata)
    if installed.get(project_name) != project_version:
        raise ValueError("installed first-party version differs from wheel metadata")

    dependencies = report.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError("audit report has no dependency records")

    seen: set[str] = set()
    audited_count = 0
    finding_count = 0
    skipped_project: str | None = None
    for dependency in dependencies:
        if not isinstance(dependency, Mapping):
            raise ValueError("audit dependency record is not an object")
        name = _normalize_name(dependency.get("name"))
        if name in seen:
            raise ValueError(f"duplicate audit dependency: {name}")
        seen.add(name)
        if name not in installed:
            raise ValueError(f"audited dependency is not installed: {name}")

        skip_reason = dependency.get("skip_reason")
        if skip_reason is not None:
            expected = f"{UNPUBLISHED_PROJECT_SKIP}{project_name} ({project_version})"
            if name != project_name or skip_reason != expected:
                raise ValueError(f"unexpected skipped dependency: {name}")
            if dependency.get("vulns"):
                raise ValueError(
                    "skipped project must not contain vulnerability findings"
                )
            if dependency.get("version") not in (None, project_version):
                raise ValueError("skipped project has incorrect version")
            skipped_project = name
            continue

        version = dependency.get("version")
        if not isinstance(version, str) or version != installed[name]:
            raise ValueError(f"audited version differs from installed version: {name}")
        vulnerabilities = dependency.get("vulns")
        if not isinstance(vulnerabilities, list):
            raise ValueError(
                f"audited dependency is missing vulnerability list: {name}"
            )
        audited_count += name != project_name
        finding_count += len(vulnerabilities)

    missing = sorted(set(installed) - seen)
    if missing:
        raise ValueError(
            "installed dependencies missing from audit: " + ", ".join(missing)
        )
    if not audited_count:
        raise ValueError("no third-party dependencies were audited")
    if finding_count:
        raise ValueError(f"audit reported findings: {finding_count}")

    return {
        "installed_dependencies": len(installed),
        "audited_dependencies": audited_count,
        "project_package_skipped": skipped_project,
        "finding_count": finding_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="pip-audit JSON report path")
    parser.add_argument("--installed-packages", type=Path, required=True)
    parser.add_argument("--wheel-metadata", type=Path, required=True)
    args = parser.parse_args()
    with args.report.open("r", encoding="utf-8") as source:
        report = json.load(source)
    with args.installed_packages.open("r", encoding="utf-8") as source:
        installed_packages = json.load(source)
    wheel_metadata = args.wheel_metadata.read_text(encoding="utf-8")
    if not isinstance(report, Mapping):
        raise ValueError("audit report root must be an object")
    result = validate_audit_report(report, installed_packages, wheel_metadata)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

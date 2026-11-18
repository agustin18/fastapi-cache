"""Validate pip-audit JSON completeness for a local project wheel profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

PROJECT_PACKAGE = "fastapi-cache-stable"
UNPUBLISHED_PROJECT_SKIP = "Dependency not found on PyPI and could not be audited:"


def validate_audit_report(
    report: Mapping[str, Any], project_package: str = PROJECT_PACKAGE
) -> dict[str, Any]:
    dependencies = report.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError("audit report has no dependency records")

    audited_count = 0
    finding_count = 0
    skipped_project: str | None = None
    for dependency in dependencies:
        if not isinstance(dependency, Mapping):
            raise ValueError("audit dependency record is not an object")
        name = dependency.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("audit dependency record has no package name")

        skip_reason = dependency.get("skip_reason")
        if skip_reason is not None:
            if (
                name != project_package
                or not isinstance(skip_reason, str)
                or not skip_reason.startswith(UNPUBLISHED_PROJECT_SKIP)
            ):
                raise ValueError("unexpected skipped dependency: " + name)
            if skipped_project is not None:
                raise ValueError("duplicate skipped first-party package record")
            skipped_project = name
            continue

        vulnerabilities = dependency.get("vulns")
        if not isinstance(vulnerabilities, list):
            raise ValueError("audited dependency record is missing its vulnerability list")
        audited_count += 1
        finding_count += len(vulnerabilities)

    if not audited_count:
        raise ValueError("no third-party dependencies were audited")
    if finding_count:
        raise ValueError(f"audit reported findings: {finding_count}")

    return {
        "audited_dependencies": audited_count,
        "project_package_skipped": skipped_project,
        "finding_count": finding_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="pip-audit JSON report path")
    args = parser.parse_args()
    with args.report.open("r", encoding="utf-8") as source:
        report = json.load(source)
    if not isinstance(report, Mapping):
        raise ValueError("audit report root must be an object")
    print(json.dumps(validate_audit_report(report), indent=2))


if __name__ == "__main__":
    main()

import pytest
from scripts.validate_security_audit import validate_audit_report


def test_validates_audit_with_only_unpublished_project_skipped() -> None:
    report = {
        "dependencies": [
            {
                "name": "fastapi-cache-stable",
                "skip_reason": (
                    "Dependency not found on PyPI and could not be audited: "
                    "fastapi-cache-stable (0.3.0rc1)"
                ),
            },
            {"name": "aiohttp", "version": "3.14.5", "vulns": []},
            {"name": "anyio", "version": "4.16.0", "vulns": []},
        ]
    }

    result = validate_audit_report(report)

    assert result == {
        "audited_dependencies": 2,
        "project_package_skipped": "fastapi-cache-stable",
        "finding_count": 0,
    }


def test_rejects_skipped_dependency_other_than_unpublished_project() -> None:
    report = {
        "dependencies": [
            {
                "name": "urllib3",
                "skip_reason": "Dependency metadata could not be collected",
            },
            {"name": "anyio", "version": "4.16.0", "vulns": []},
        ]
    }

    with pytest.raises(ValueError, match="unexpected skipped dependency: urllib3"):
        validate_audit_report(report)


def test_rejects_report_with_vulnerability_findings() -> None:
    report = {
        "dependencies": [
            {
                "name": "aiohttp",
                "version": "3.9.5",
                "vulns": [{"id": "GHSA-example"}],
            }
        ]
    }

    with pytest.raises(ValueError, match="audit reported findings"):
        validate_audit_report(report)


def test_rejects_report_without_any_audited_dependencies() -> None:
    report = {
        "dependencies": [
            {
                "name": "fastapi-cache-stable",
                "skip_reason": (
                    "Dependency not found on PyPI and could not be audited: "
                    "fastapi-cache-stable (0.3.0rc1)"
                ),
            }
        ]
    }

    with pytest.raises(ValueError, match="no third-party dependencies were audited"):
        validate_audit_report(report)

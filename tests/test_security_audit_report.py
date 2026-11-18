"""Adversarial coverage checks for the wheel-profile pip-audit validator."""

from __future__ import annotations

from copy import deepcopy

import pytest
from scripts.validate_security_audit import validate_audit_report

WHEEL_METADATA = (
    "Metadata-Version: 2.4\n"
    "Name: fastapi-cache-stable\n"
    "Version: 0.3.0rc1\n"
)


@pytest.fixture
def profile() -> tuple[dict, list[dict]]:
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
            {"name": "AnyIO", "version": "4.16.0", "vulns": []},
            {"name": "pydantic_core", "version": "2.50.4", "vulns": []},
        ]
    }
    installed = [
        {"name": "fastapi_cache_stable", "version": "0.3.0rc1"},
        {"name": "aiohttp", "version": "3.14.5"},
        {"name": "anyio", "version": "4.16.0"},
        {"name": "pydantic-core", "version": "2.50.4"},
    ]
    return report, installed


def validate(profile: tuple[dict, list[dict]]) -> dict:
    return validate_audit_report(*profile, WHEEL_METADATA)


def test_validates_exact_complete_profile(profile: tuple[dict, list[dict]]) -> None:
    assert validate(profile) == {
        "installed_dependencies": 4,
        "audited_dependencies": 3,
        "project_package_skipped": "fastapi-cache-stable",
        "finding_count": 0,
    }


def test_also_allows_first_party_when_audited_successfully(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[0]["dependencies"][0] = {
        "name": "fastapi-cache-stable", "version": "0.3.0rc1", "vulns": []
    }
    assert validate(profile)["project_package_skipped"] is None


def test_rejects_a_truncated_report(profile: tuple[dict, list[dict]]) -> None:
    profile[0]["dependencies"].pop()
    with pytest.raises(ValueError, match="missing from audit: pydantic-core"):
        validate(profile)


def test_rejects_a_report_with_only_one_dependency(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[0]["dependencies"] = profile[0]["dependencies"][1:2]
    with pytest.raises(ValueError, match="missing from audit"):
        validate(profile)


def test_rejects_unexpected_audit_dependency(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[0]["dependencies"].append(
        {"name": "urllib3", "version": "2.8.0", "vulns": []}
    )
    with pytest.raises(ValueError, match="not installed: urllib3"):
        validate(profile)


def test_rejects_duplicate_report_name_even_with_alias(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[0]["dependencies"].append(
        {"name": "pydantic-core", "version": "2.50.4", "vulns": []}
    )
    with pytest.raises(ValueError, match="duplicate audit dependency"):
        validate(profile)


def test_rejects_duplicate_inventory_name_even_with_alias(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[1].append({"name": "FASTAPI.CACHE.STABLE", "version": "0.3.0rc1"})
    with pytest.raises(ValueError, match="duplicate installed package"):
        validate(profile)


def test_rejects_version_mismatch(profile: tuple[dict, list[dict]]) -> None:
    profile[0]["dependencies"][2]["version"] = "4.4.0"
    with pytest.raises(ValueError, match="version differs.*anyio"):
        validate(profile)


def test_rejects_missing_audited_version(profile: tuple[dict, list[dict]]) -> None:
    del profile[0]["dependencies"][1]["version"]
    with pytest.raises(ValueError, match="version differs.*aiohttp"):
        validate(profile)


def test_rejects_skipped_third_party(profile: tuple[dict, list[dict]]) -> None:
    profile[0]["dependencies"][1] = {
        "name": "aiohttp", "skip_reason": "Dependency metadata could not be collected"
    }
    with pytest.raises(ValueError, match="unexpected skipped dependency: aiohttp"):
        validate(profile)


def test_rejects_wrong_first_party_skip_reason(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[0]["dependencies"][0]["skip_reason"] = (
        "Dependency metadata could not be collected"
    )
    with pytest.raises(ValueError, match="unexpected skipped dependency"):
        validate(profile)


def test_rejects_first_party_skip_for_other_version(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[0]["dependencies"][0]["skip_reason"] = (
        "Dependency not found on PyPI and could not be audited: "
        "fastapi-cache-stable (0.3.0b1)"
    )
    with pytest.raises(ValueError, match="unexpected skipped dependency"):
        validate(profile)


def test_rejects_missing_first_party_record(profile: tuple[dict, list[dict]]) -> None:
    profile[0]["dependencies"].pop(0)
    with pytest.raises(ValueError, match="missing from audit: fastapi-cache-stable"):
        validate(profile)


def test_rejects_installed_first_party_version_mismatch(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[1][0]["version"] = "0.3.0b1"
    with pytest.raises(ValueError, match="first-party version differs"):
        validate(profile)


def test_rejects_bad_wheel_metadata(profile: tuple[dict, list[dict]]) -> None:
    with pytest.raises(ValueError, match="unexpected project wheel"):
        validate_audit_report(*profile, "Name: other\nVersion: 0.3.0rc1\n")


def test_rejects_vulnerability_findings(profile: tuple[dict, list[dict]]) -> None:
    profile[0]["dependencies"][1]["vulns"] = [{"id": "GHSA-example"}]
    with pytest.raises(ValueError, match="audit reported findings: 1"):
        validate(profile)


def test_rejects_missing_vulns_list(profile: tuple[dict, list[dict]]) -> None:
    del profile[0]["dependencies"][1]["vulns"]
    with pytest.raises(ValueError, match="missing vulnerability list: aiohttp"):
        validate(profile)


def test_rejects_skipped_project_with_vulnerability_findings(
    profile: tuple[dict, list[dict]],
) -> None:
    profile[0]["dependencies"][0]["vulns"] = [{"id": "GHSA-example"}]
    with pytest.raises(ValueError, match="skipped project must not"):
        validate(profile)


def test_rejects_empty_installed_inventory(profile: tuple[dict, list[dict]]) -> None:
    profile[1].clear()
    with pytest.raises(ValueError, match="inventory is empty"):
        validate(profile)


def test_rejects_duplicate_metadata_name(profile: tuple[dict, list[dict]]) -> None:
    with pytest.raises(ValueError, match="exactly one Name and Version"):
        validate_audit_report(*profile, WHEEL_METADATA + "Name: other\n")


def test_rejects_invalid_report_root(profile: tuple[dict, list[dict]]) -> None:
    with pytest.raises(ValueError, match="no dependency records"):
        validate_audit_report({"dependencies": "incorrect"}, profile[1], WHEEL_METADATA)


def test_profile_inputs_are_not_mutated(profile: tuple[dict, list[dict]]) -> None:
    original = deepcopy(profile)
    validate(profile)
    assert profile == original

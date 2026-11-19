from importlib.metadata import metadata

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version


def test_requires_python_matches_stable_support_policy() -> None:
    assert metadata("fastapi-cache-stable")["Requires-Python"] == ">=3.8,<3.14"


def test_python_classifiers_match_stable_support_policy() -> None:
    package_metadata = metadata("fastapi-cache-stable")
    python_classifiers = {
        classifier
        for classifier in package_metadata.get_all("Classifier") or []
        if classifier.startswith("Programming Language :: Python :: 3.")
    }

    assert python_classifiers == {
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    }


def test_uvicorn_is_not_published_as_requirement() -> None:
    requirements = [
        Requirement(value)
        for value in metadata("fastapi-cache-stable").get_all("Requires-Dist") or []
    ]
    assert all(canonicalize_name(req.name) != "uvicorn" for req in requirements)


def test_jinja2_remains_a_mandatory_runtime_requirement() -> None:
    requirements = [
        Requirement(value)
        for value in metadata("fastapi-cache-stable").get_all("Requires-Dist") or []
    ]
    jinja2_requirements = [
        req for req in requirements if canonicalize_name(req.name) == "jinja2"
    ]
    assert len(jinja2_requirements) == 1
    requirement = jinja2_requirements[0]
    assert requirement.marker is None or requirement.marker.evaluate({"extra": ""})
    assert Version("3.0") in requirement.specifier


def test_dynamodb_extra_is_excluded_from_legacy_python_profiles() -> None:
    requirements = [
        Requirement(requirement)
        for requirement in metadata("fastapi-cache-stable").get_all(
            "Requires-Dist"
        )
        or []
    ]

    def has_requirement(name: str, extra: str, python_version: str) -> bool:
        environment = {
            "extra": extra,
            "python_version": python_version,
            "python_full_version": python_version + ".0",
        }
        return any(
            requirement.name.lower() == name
            and (
                requirement.marker is None
                or requirement.marker.evaluate(environment)
            )
            for requirement in requirements
        )

    for python_version in ("3.8", "3.9"):
        assert not has_requirement("aiobotocore", "dynamodb", python_version)
        assert not has_requirement("aiohttp", "dynamodb", python_version)
        assert not has_requirement("aiobotocore", "all", python_version)
        assert not has_requirement("aiohttp", "all", python_version)

    for python_version in ("3.10", "3.11", "3.12", "3.13"):
        assert has_requirement("aiobotocore", "dynamodb", python_version)
        assert has_requirement("aiohttp", "dynamodb", python_version)
        assert has_requirement("aiobotocore", "all", python_version)
        assert has_requirement("aiohttp", "all", python_version)

    for extra in ("dynamodb", "all"):
        aiohttp_extra = [
            requirement
            for requirement in requirements
            if requirement.name.lower() == "aiohttp"
            and requirement.marker is not None
            and requirement.marker.evaluate(
                {
                    "extra": extra,
                    "python_version": "3.10",
                    "python_full_version": "3.10.0",
                }
            )
        ]
        assert aiohttp_extra
        assert all(
            Version("3.14.4") in requirement.specifier
            for requirement in aiohttp_extra
        )
    assert not any(
        requirement.name.lower() == "anyio" for requirement in requirements
    )

from importlib.metadata import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version


def test_requires_python_matches_stable_support_policy() -> None:
    assert metadata("fastapi-cache-stable")["Requires-Python"] == ">=3.8,<3.15"


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
        "Programming Language :: Python :: 3.14",
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

    for python_version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
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



def test_redis_extra_has_exactly_one_python_conditional_requirement() -> None:
    """The published wheel must never require two Redis client series at once."""
    requirements = [
        Requirement(value)
        for value in metadata("fastapi-cache-stable").get_all("Requires-Dist") or []
        if canonicalize_name(Requirement(value).name) == "redis"
    ]
    assert len(requirements) == 3  # three windows; each marker serves redis/all

    cases = {
        "3.8": (Version("6.1.1"), Version("6.2.0")),
        "3.9": (Version("7.0.1"), Version("7.1.0")),
        "3.10": (Version("8.1.0"), Version("8.2.0")),
        "3.11": (Version("8.1.0"), Version("8.2.0")),
        "3.12": (Version("8.1.0"), Version("8.2.0")),
        "3.13": (Version("8.1.0"), Version("8.2.0")),
        "3.14": (Version("8.1.0"), Version("8.2.0")),
    }

    for python, (latest_allowed, first_excluded) in cases.items():
        for extra in ("redis", "all"):
            environment = {
                "python_version": python,
                "python_full_version": python + ".0",
                "extra": extra,
            }
            active = [
                requirement
                for requirement in requirements
                if requirement.marker is not None
                and requirement.marker.evaluate(environment)
            ]
            assert len(active) == 1, (python, extra, active)
            requirement = active[0]
            assert Version("4.6.0") in requirement.specifier
            assert latest_allowed in requirement.specifier
            assert first_excluded not in requirement.specifier

    for python, extra in (
        ("3.8", ""),
        ("3.9", ""),
        ("3.10", ""),
        ("3.13", ""),
        ("3.14", ""),
        ("3.15", "redis"),
        ("3.15", "all"),
    ):
        environment = {
            "python_version": python,
            "python_full_version": python + ".0",
            "extra": extra,
        }
        assert not any(
            requirement.marker is None
            or requirement.marker.evaluate(environment)
            for requirement in requirements
        ), (python, extra)


def test_redis_is_never_mandatory_without_an_extra() -> None:
    requirements = [
        Requirement(value)
        for value in metadata("fastapi-cache-stable").get_all("Requires-Dist") or []
        if canonicalize_name(Requirement(value).name) == "redis"
    ]
    for python in ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"):
        assert not any(
            requirement.marker is None
            or requirement.marker.evaluate(
                {
                    "extra": "",
                    "python_version": python,
                    "python_full_version": python + ".0",
                }
            )
            for requirement in requirements
        )


def test_packaged_readme_is_release_specific() -> None:
    package = metadata("fastapi-cache-stable")
    description = package.get_payload()
    version = package["Version"]
    assert f"fastapi-cache-stable {version}" in description
    assert f"fastapi-cache-stable[redis]=={version}" in description
    assert "CacheConfig" in description
    assert "CacheFailurePolicy" in description
    assert "Latest published stable" not in description
    assert "fastapi-cache-stable==0.7.2" not in description


def test_pyproject_points_poetry_at_release_readme() -> None:
    source = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'readme = "README_PYPI.md"' in source
    assert '"README_PYPI.md",' in source

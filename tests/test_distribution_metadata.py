from importlib.metadata import metadata


def test_requires_python_matches_stable_support_policy() -> None:
    assert metadata("fastapi-cache-stable")["Requires-Python"] == ">=3.11,<3.14"


def test_python_classifiers_match_stable_support_policy() -> None:
    package_metadata = metadata("fastapi-cache-stable")
    python_classifiers = {
        classifier
        for classifier in package_metadata.get_all("Classifier") or []
        if classifier.startswith("Programming Language :: Python :: 3.")
    }

    assert python_classifiers == {
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    }

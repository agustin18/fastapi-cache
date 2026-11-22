"""Test the isolated published benchmark execution policy, not performance."""

from pathlib import Path

import pytest
from benchmarks.runner import VERSION, WHEEL_SHA256, validate_redis_url


def test_historical_published_wheel_identity_is_pinned() -> None:
    assert VERSION == "0.6.0"
    assert WHEEL_SHA256 == "60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e"


@pytest.mark.parametrize("url", [
    "redis://cache.internal:6379/15", "redis://127.0.0.1:6379/0",
    "redis://username:password@127.0.0.1:6379/15",
    "rediss://127.0.0.1:6379/15", "redis://127.0.0.1:6379/15?x=1",
    "redis://127.0.0.1/15", "redis://127.0.0.1:6379/15#fragment",
])
def test_no_remote_or_ambiguous_redis_targets(url: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        validate_redis_url(url)


def test_benchmark_scripts_are_never_packaged_as_runtime_code() -> None:
    root = Path(__file__).resolve().parents[1]
    project = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'include = "fastapi_cache"' in project
    assert 'include = "benchmarks"' not in project
    workload = (root / "benchmarks/workload.py").read_text(encoding="utf-8")
    assert "metadata.version(\"fastapi-cache-stable\")" in workload
    assert '"site-packages" in path.parts' in workload

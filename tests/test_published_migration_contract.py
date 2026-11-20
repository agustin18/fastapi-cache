"""Protect published migration golden and the isolated CI comparison."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

from fastapi_cache.key_builder import default_key_builder
from tests import published_migration_compare

ROOT = Path(__file__).resolve().parents[1]


def test_published_default_key_golden_remains_bit_compatible() -> None:
    def sample_endpoint() -> None:
        pass

    # Reproduce a published consumer executed via python -I ... .py.
    sample_endpoint.__module__ = "__main__"
    encoded = "__main__:sample_endpoint:(7,):{'lang': 'es'}"
    digest = hashlib.md5(encoded.encode()).hexdigest()  # noqa: S324
    assert digest == "6c5186afe53d101dea5118bda9aebbcf"
    actual = default_key_builder(
        sample_endpoint,
        "migration-parity:ordinary",
        args=(7,),
        kwargs={"lang": "es"},
    )
    assert actual == f"migration-parity:ordinary:{digest}"


def test_workflow_uses_separate_published_py_p_i_providers() -> None:
    workflow = (
        ROOT / ".github/workflows/migration-published-parity.yml"
    ).read_text()
    assert 'fastapi-cache2==0.2.2' in workflow
    assert 'fastapi-cache-stable==0.4.1' in workflow
    assert 'python: ["3.11", "3.12"]' in workflow
    assert '"$RUNNER_TEMP/legacy/bin/python" -I' in workflow
    assert '"$RUNNER_TEMP/stable/bin/python" -I' in workflow
    assert 'pip check' in workflow
    assert "migration_redis_e2e.py" in workflow
    assert "published_migration_compare.py" in workflow
    assert "redis_consumer_probe.py" in workflow
    assert "pypi-wheel-sha256.txt" in workflow
    assert "retention-days: 90" in workflow
    assert "gh-action-pypi-publish" not in workflow
    assert "id-token: write" not in workflow


@pytest.fixture
def parity_records() -> tuple[dict, dict]:
    common = {
        "golden_default_key":
            "migration-parity:ordinary:6c5186afe53d101dea5118bda9aebbcf",
        "ordinary": ["MISS", "HIT"],
        "sync": ["MISS", "HIT"],
        "conditional_304": 304,
        "module_location": "/tmp/sample-venv/lib/python3.11/site-packages/fastapi_cache/__init__.py",
    }
    old = {
        **common,
        "distribution": "fastapi-cache2",
        "version": "0.2.2",
        "variant": {"values": ["en", "en"], "statuses": ["MISS", "HIT"]},
        "authentication": {
            "values": ["Bearer Alice", "Bearer Alice"],
            "statuses": ["MISS", "HIT"],
        },
    }
    new = {
        **common,
        "distribution": "fastapi-cache-stable",
        "version": "0.4.1",
        "variant": {"values": ["en", "es"], "statuses": [None, None]},
        "authentication": {
            "values": ["Bearer Alice", "Bearer Bob"],
            "statuses": [None, None],
        },
        "error": {"http_statuses": [418, 418], "statuses": [None, None]},
        "etag": 'W/"fake-sha256"',
    }
    return old, new


def _run_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    old: dict,
    new: dict,
) -> None:
    legacy_path, stable_path = tmp_path / "legacy.json", tmp_path / "stable.json"
    legacy_path.write_text(json.dumps(old))
    stable_path.write_text(json.dumps(new))
    monkeypatch.setattr(
        sys,
        "argv",
        ["published_migration_compare.py", str(legacy_path), str(stable_path)],
    )
    published_migration_compare.main()


def test_golden_compare_accepts_intentional_safe_delta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parity_records: tuple[dict, dict],
) -> None:
    _run_comparison(tmp_path, monkeypatch, *parity_records)


def test_golden_compare_fails_on_stable_private_cache_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parity_records: tuple[dict, dict],
) -> None:
    old, new = parity_records
    new["authentication"]["values"][1] = "Bearer Alice"
    with pytest.raises(AssertionError):
        _run_comparison(tmp_path, monkeypatch, old, new)


def test_golden_compare_fails_on_legacy_key_format_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parity_records: tuple[dict, dict],
) -> None:
    old, new = parity_records
    new["golden_default_key"] = "new-format:rotated"
    with pytest.raises(AssertionError):
        _run_comparison(tmp_path, monkeypatch, old, new)

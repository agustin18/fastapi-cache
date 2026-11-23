"""Pure, network-free contracts for fair installed-release comparisons."""

import json
from pathlib import Path

import pytest
from benchmarks.compare_versions import (
    WHEEL_HASHES,
    aggregate_comparison,
    comparison_schedule,
)


def test_release_artifact_hashes_are_immutable() -> None:
    assert WHEEL_HASHES == {
        "0.5.0": "7f30d074e222aaf4471d13105e1282b97d2968549bc4b727b941837272b10449",
        "0.6.0": "60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e",
    }


def test_balanced_abba_order() -> None:
    assert comparison_schedule(4) == [
        ("0.5.0", "0.6.0"), ("0.6.0", "0.5.0"),
        ("0.5.0", "0.6.0"), ("0.6.0", "0.5.0"),
    ]


@pytest.mark.parametrize("invalid", [0, -1, 1, 3, 5, 7, 8])
def test_reject_unbalanced_or_unbounded_repeats(invalid: int) -> None:
    with pytest.raises(ValueError, match="2, 4 or 6"):
        comparison_schedule(invalid)


def _fixture(out: Path, version: str, pair: int, ms: float) -> None:
    folder = out / version / ("pair-%02d" % pair)
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {"cache_distribution": version},
        "cases": {
            "http_inmemory_hit_small": {
                "samples": 120, "p50_ms": ms, "p95_ms": ms * 2,
                "p99_ms": ms * 3,
            }
        },
    }
    (folder / "summary.json").write_text(json.dumps(payload), encoding="utf-8")


def test_comparison_pairs_and_exact_metadata(tmp_path: Path) -> None:
    for index in (1, 2):
        _fixture(tmp_path, "0.5.0", index, 1.0)
        _fixture(tmp_path, "0.6.0", index, 1.5)
    report = aggregate_comparison(tmp_path, 2)
    assert report["pair_count_per_version"] == 2
    assert report["cases"]["http_inmemory_hit_small"]["p50_ms"][
        "median_paired_ratio"
    ] == 1.5
    assert report["cases"]["http_inmemory_hit_small"]["per_run_samples"] == [120] * 4
    assert json.loads((tmp_path / "comparison.json").read_text()) == report


def test_comparison_rejects_mismatched_report_versions(tmp_path: Path) -> None:
    for index in (1, 2):
        _fixture(tmp_path, "0.5.0", index, 1.0)
        _fixture(tmp_path, "0.6.0", index, 1.5)
    target = tmp_path / "0.5.0" / "pair-02" / "summary.json"
    bad = json.loads(target.read_text())
    bad["metadata"]["cache_distribution"] = "0.6.0"
    target.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="Installed version"):
        aggregate_comparison(tmp_path, 2)

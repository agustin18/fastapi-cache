"""Unit checks for repeated installed-distribution measurement aggregation."""

import json
from pathlib import Path

import pytest
from benchmarks.aggregate import aggregate_results


def _write(folder: Path, *, latency: float, extra: bool = False) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    cases = {
        "http_inmemory_hit_small": {
            "samples": 120, "p50_ms": latency,
            "p95_ms": latency * 2, "p99_ms": latency * 3,
        },
        "http_inmemory_ttl_expired": {
            "samples": 1, "p50_ms": latency,
            "p95_ms": latency, "p99_ms": latency,
        },
    }
    if extra:
        cases["unexpected"] = cases["http_inmemory_hit_small"]
    data = {
        "metadata": {"resource_usage": {
            "process_cpu_seconds": latency, "process_wall_seconds": latency + 1,
            "rss_kib": 22000, "peak_rss_kib": 25000,
        }},
        "cases": cases,
    }
    (folder / "summary.json").write_text(json.dumps(data), encoding="utf-8")


def test_aggregate_variance_and_sample_sufficiency(tmp_path: Path) -> None:
    _write(tmp_path, latency=1.0)
    _write(tmp_path / "runs" / "run-02", latency=2.0)
    _write(tmp_path / "runs" / "run-03", latency=3.0)
    report = aggregate_results(tmp_path, repeats=3)
    assert report["repeats"] == 3
    hit = report["cases"]["http_inmemory_hit_small"]
    assert hit["p50_ms"]["median"] == 2.0
    assert hit["p50_ms"]["stdev"] == 1.0
    assert hit["samples_per_run"] == [120, 120, 120]
    assert hit["p99_interpretation"] == "at-least-100-samples-per-run"
    assert "insufficient" in report["cases"]["http_inmemory_ttl_expired"]["p99_interpretation"]
    assert report["resource_usage"]["peak_rss_kib"]["median"] == 25000
    assert json.loads((tmp_path / "aggregate.json").read_text()) == report


def test_aggregate_refuses_incomparable_case_sets(tmp_path: Path) -> None:
    _write(tmp_path, latency=1.0)
    _write(tmp_path / "runs" / "run-02", latency=2.0, extra=True)
    with pytest.raises(ValueError, match="Different cases"):
        aggregate_results(tmp_path, repeats=2)


@pytest.mark.parametrize("count", [0, -1, 6])
def test_aggregate_rejects_unsafe_run_counts(tmp_path: Path, count: int) -> None:
    with pytest.raises(ValueError, match="1-5"):
        aggregate_results(tmp_path, repeats=count)

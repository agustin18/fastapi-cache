"""Aggregate independent benchmark process runs without performance claims.

Percentile variance is measured *across runs*, never inferred from individual
operation samples as if they were independent machine measurements.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any


def aggregate_results(output: Path, repeats: int) -> dict[str, Any]:
    if not 1 <= repeats <= 5:
        raise ValueError("Expected 1-5 isolated benchmark processes")
    documents: list[dict[str, Any]] = []
    for index in range(repeats):
        folder = output if index == 0 else output / "runs" / f"run-{index + 1:02d}"
        item = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        if not isinstance(item, dict) or not item.get("cases"):
            raise ValueError(f"No benchmark cases in run {index + 1}")
        documents.append(item)

    expected = set(documents[0]["cases"])
    if any(set(doc["cases"]) != expected for doc in documents[1:]):
        raise ValueError("Different cases between benchmark runs; cannot compare")

    def distribution(numbers: list[float]) -> dict[str, Any]:
        mean = statistics.mean(numbers)
        return {
            "median": statistics.median(numbers),
            "mean": mean,
            "stdev": statistics.stdev(numbers) if len(numbers) > 1 else None,
            "cv_pct": (statistics.stdev(numbers) / mean * 100)
            if len(numbers) > 1 and mean > 0 else None,
            "individual_runs": numbers,
        }

    cases: dict[str, Any] = {}
    for case in sorted(expected):
        rows = [doc["cases"][case] for doc in documents]
        sample_counts = [int(row["samples"]) for row in rows]
        cases[case] = {
            "samples_per_run": sample_counts,
            "p99_interpretation": (
                "at-least-100-samples-per-run" if min(sample_counts) >= 100
                else "insufficient-per-run-samples-for-reliable-tail-claim"
            ),
            "p50_ms": distribution([float(row["p50_ms"]) for row in rows]),
            "p95_ms": distribution([float(row["p95_ms"]) for row in rows]),
            "p99_ms": distribution([float(row["p99_ms"]) for row in rows]),
        }

    resources: dict[str, Any] = {}
    for key in ("process_cpu_seconds", "process_wall_seconds", "rss_kib", "peak_rss_kib"):
        values = [doc["metadata"].get("resource_usage", {}).get(key) for doc in documents]
        if all(isinstance(val, (float, int)) and val >= 0 for val in values):
            resources[key] = distribution([float(val) for val in values])
        else:
            resources[key] = None

    report: dict[str, Any] = {
        "schema": "benchmark-repetitions-v1",
        "repeats": repeats,
        "cases": cases,
        "resource_usage": resources,
        "interpretation": (
            "Percentiles are in-process measurements, variance is across fresh "
            "processes on the same worker. Run-to-run CV is descriptive, not an "
            "approved budget or an inference of production p99."
        ),
    }
    (output / "aggregate.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report

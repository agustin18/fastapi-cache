"""Aggregate preregistered C4 rounds without an automatic timing verdict."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

MODES = ("published", "candidate-legacy", "scoped-off", "scoped-on")
ORDER = tuple(MODES[i:] + MODES[:i] for i in range(len(MODES)))


def aggregate(
    root: Path, profile: str = "full", baseline_version: str = "0.7.2",
) -> dict[str, Any]:
    if profile not in ("full", "smoke") or baseline_version not in ("0.7.2", "0.8.0"):
        raise ValueError("Unsupported C4 comparison")
    order = ORDER if profile == "full" else ORDER[:1]
    samples = 120 if profile == "full" else 24
    metrics_to_compare = (
        ("p50_ms", "p95_ms", "p99_ms", "requests_per_second")
        if profile == "full" else ("p50_ms", "requests_per_second")
    )
    runs = {
        mode: [json.loads((root / f"round-{i + 1}" / mode / "summary.json").read_text(encoding="utf-8"))
               for i in range(len(order))]
        for mode in MODES
    }
    cases = set(runs["published"][0]["cases"])
    if not cases:
        raise ValueError("No cases")
    for mode, summaries in runs.items():
        for item in summaries:
            if item["mode"] != mode or set(item["cases"]) != cases:
                raise ValueError("Invalid comparison identity or missing case")
            if item.get("profile", "full") != profile or item.get("baseline_version", "0.7.2") != baseline_version:
                raise ValueError("Mismatched comparison profile or baseline")
            if any(case["samples"] != samples for case in item["cases"].values()):
                raise ValueError("Insufficient samples")
    result: dict[str, Any] = {}
    for case in sorted(cases):
        comparisons = {}
        for left, right in (
            ("published", "candidate-legacy"),
            ("candidate-legacy", "scoped-off"),
            ("scoped-off", "scoped-on"),
        ):
            metrics = {}
            for metric in metrics_to_compare:
                a = [float(run["cases"][case][metric]) for run in runs[left]]
                b = [float(run["cases"][case][metric]) for run in runs[right]]
                if min(a + b) <= 0:
                    raise ValueError("Nonpositive measurement")
                ratios = [y / x for x, y in zip(a, b)]
                metrics[metric] = {
                    "baseline_median": statistics.median(a),
                    "candidate_median": statistics.median(b),
                    "paired_ratios": ratios,
                    "median_paired_ratio": statistics.median(ratios),
                    "ratio_stdev": statistics.stdev(ratios) if len(ratios) > 1 else None,
                }
            comparisons[left + "_to_" + right] = metrics
        result[case] = comparisons
    return {
        "schema": "c4-descriptive-v1" if profile == "full" else "c4-smoke-v1",
        "profile": profile, "baseline_version": baseline_version,
        "order": order, "cases": result,
        "resources": {
            mode: [{k: run[k] for k in ("cpu_seconds", "wall_seconds", "peak_process_rss_kib", "lifecycle")}
                   for run in summaries]
            for mode, summaries in runs.items()
        },
        "decision": "INCONCLUSIVE for performance certification; descriptive evidence only",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--profile", choices=("full", "smoke"), default="full")
    parser.add_argument("--baseline-version", choices=("0.7.2", "0.8.0"), default="0.7.2")
    args = parser.parse_args()
    result = aggregate(args.root, args.profile, args.baseline_version)
    (args.root / "comparison.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name in ("inmemory/asgi/hit-128", "redis/tcp/hit-128"):
        print(name)
        for comparison, metrics in result["cases"][name].items():
            print(comparison, "p50 ratio", round(metrics["p50_ms"]["median_paired_ratio"], 3))
    print(result["decision"])


if __name__ == "__main__":
    main()

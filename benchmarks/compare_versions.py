"""Controlled historical comparison using *published* 0.5.0 and 0.6.0 wheels.

Never benchmarks source checkout. Versions run in independent, pinned
environments on one worker; AB/BA order balances simple temporal drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any

WHEEL_HASHES = {
    "0.5.0": "7f30d074e222aaf4471d13105e1282b97d2968549bc4b727b941837272b10449",
    "0.6.0": "60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e",
}
PACKAGE = "fastapi-cache-stable"
WORKLOAD = Path(__file__).with_name("compare_workload.py").resolve()
VERSIONS = ("0.5.0", "0.6.0")


def comparison_schedule(repeats: int) -> list[tuple[str, str]]:
    """Balanced AB/BA order; refuse an odd number of one-sided pairs."""
    if repeats not in (2, 4, 6):
        raise ValueError("Paired comparison requires 2, 4 or 6 repeats per version")
    return [
        VERSIONS if index % 2 == 0 else (VERSIONS[1], VERSIONS[0])
        for index in range(repeats)
    ]


def aggregate_comparison(output: Path, repeats: int) -> dict[str, Any]:
    schedule = comparison_schedule(repeats)
    summaries: dict[str, list[dict[str, Any]]] = {version: [] for version in VERSIONS}
    for pair_index, _ in enumerate(schedule, start=1):
        for version in VERSIONS:
            path = output / version / ("pair-%02d" % pair_index) / "summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            if summary["metadata"]["cache_distribution"] != version:
                raise ValueError("Installed version disagrees with recorded scenario")
            summaries[version].append(summary)
    cases = set(summaries[VERSIONS[0]][0]["cases"])
    if not cases:
        raise ValueError("No comparison cases")
    for version in VERSIONS:
        if any(set(summary["cases"]) != cases for summary in summaries[version]):
            raise ValueError("Different case sets between comparable runs")

    results: dict[str, Any] = {}
    for case in sorted(cases):
        metric: dict[str, Any] = {}
        for field in ("p50_ms", "p95_ms", "p99_ms"):
            older = [float(s["cases"][case][field]) for s in summaries["0.5.0"]]
            newer = [float(s["cases"][case][field]) for s in summaries["0.6.0"]]
            if min(older + newer) <= 0:
                raise ValueError("Non-positive timing measurements")
            ratios = [newer[i] / older[i] for i in range(repeats)]
            metric[field] = {
                "baseline_0_5_median_ms": statistics.median(older),
                "current_0_6_median_ms": statistics.median(newer),
                "paired_ratios_0_6_over_0_5": ratios,
                "median_paired_ratio": statistics.median(ratios),
                "paired_ratio_stdev": statistics.stdev(ratios),
                "interpretation": "descriptive, no approved performance budget",
            }
        counts = [
            int(summary["cases"][case]["samples"])
            for version in VERSIONS for summary in summaries[version]
        ]
        results[case] = {
            "per_run_samples": counts,
            "p99_tail_claim": "descriptive-only" if min(counts) >= 100 else "insufficient-samples",
            **metric,
        }
    document: dict[str, Any] = {
        "schema": "historical-installed-wheels-v1",
        "versions": list(VERSIONS),
        "wheel_sha256": WHEEL_HASHES,
        "pair_count_per_version": repeats,
        "pair_order": [list(pair) for pair in schedule],
        "cases": results,
        "limitations": (
            "AB/BA on one shared runner: NOT a causal claim, a production "
            "latency benchmark, or a reason to merge a feature automatically."
        ),
    }
    (output / "comparison.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return document


def main() -> None:
    # Resolve the existing trusted runner only from within benchmarks/.
    from runner import FRAMEWORK, _run, _venv_python, validate_redis_url

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--redis-url", default="redis://127.0.0.1:6379/15")
    parser.add_argument("--repeats", type=int, default=4)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("This comparison is pinned to CPython 3.12")
    order = comparison_schedule(args.repeats)
    url = validate_redis_url(args.redis_url)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    freezes: dict[str, list[str]] = {}
    provenance: dict[str, Any] = {"framework_pins": list(FRAMEWORK), "wheels": {}}

    with tempfile.TemporaryDirectory(prefix="historical-versions-") as tmp:
        root = Path(tmp)
        executables: dict[str, Path] = {}
        for version in VERSIONS:
            environment = root / ("venv-" + version)
            venv.EnvBuilder(with_pip=True).create(str(environment))
            py = _venv_python(environment)
            wheels_folder = root / ("wheel-" + version)
            wheels_folder.mkdir()
            _run([str(py), "-m", "pip", "download", "--disable-pip-version-check",
                  "--no-cache-dir", "--no-deps", "--only-binary=:all:",
                  "--dest", str(wheels_folder), f"{PACKAGE}=={version}"], root)
            wheels = list(wheels_folder.glob("*.whl"))
            if len(wheels) != 1:
                raise RuntimeError("Exactly one published wheel is required")
            digest = hashlib.sha256(wheels[0].read_bytes()).hexdigest()
            if digest != WHEEL_HASHES[version]:
                raise RuntimeError(f"Historical wheel digest mismatch for {version}")
            _run([str(py), "-m", "pip", "install", "--disable-pip-version-check",
                  "--no-cache-dir", str(wheels[0]), *FRAMEWORK], root)
            _run([str(py), "-m", "pip", "check"], root)
            freeze = _run([str(py), "-m", "pip", "freeze"], root)
            (out / version).mkdir(exist_ok=True)
            (out / version / "pip-freeze.txt").write_text(freeze, encoding="utf-8")
            freezes[version] = sorted(
                line for line in freeze.splitlines()
                if not line.lower().startswith("fastapi-cache-stable")
            )
            provenance["wheels"][version] = {
                "filename": wheels[0].name, "sha256": digest,
            }
            executables[version] = py

        if freezes["0.5.0"] != freezes["0.6.0"]:
            raise RuntimeError(
                "Resolved dependencies differ: refusing uncontrolled comparison"
            )

        for index, pair in enumerate(order, start=1):
            for version in pair:
                destination = out / version / ("pair-%02d" % index)
                destination.mkdir(parents=True, exist_ok=True)
                print(f"Compare pair {index}/{len(order)}: wheel {version}", flush=True)
                _run([str(executables[version]), "-I", str(WORKLOAD),
                      "--expected-version", version, "--redis-url", url,
                      "--output", str(destination)], root)
    provenance["same_resolved_dependencies"] = True
    provenance["python"] = sys.version.split()[0]
    provenance["pair_schedule"] = [list(x) for x in order]
    (out / "provenance.json").write_text(
        json.dumps(provenance, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    report = aggregate_comparison(out, args.repeats)
    print(
        "Compared", len(report["cases"]), "shared-interface cases across",
        args.repeats, "balanced pairs; no performance decision made",
    )


if __name__ == "__main__":
    main()

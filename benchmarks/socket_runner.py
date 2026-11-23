"""Run the real TCP HTTP workload on a verified published or local candidate wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import venv
from pathlib import Path

from aggregate import aggregate_results
from candidate_artifact import verify_candidate_wheel
from runner import (
    FRAMEWORK,
    PACKAGE,
    VERSION,
    WHEEL_SHA256,
    _run,
    _venv_python,
    validate_redis_url,
)

WORKLOAD = Path(__file__).with_name("socket_workload.py").resolve()
UVICORN = "uvicorn==0.34.2"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--redis-url", default="redis://127.0.0.1:6379/15")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=120)
    parser.add_argument("--candidate-wheel", type=Path)
    parser.add_argument("--candidate-version")
    parser.add_argument("--candidate-sha256")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("This profile uses CPython 3.12")
    if not 1 <= args.repeats <= 3:
        parser.error("Repeats must be 1..3 isolated workload processes")
    if not 100 <= args.iterations <= 1000:
        parser.error("Iterations must be 100..1000 for each latency case")
    candidate_flags = (
        args.candidate_wheel, args.candidate_version, args.candidate_sha256
    )
    if any(item is not None for item in candidate_flags) and not all(
        item is not None for item in candidate_flags
    ):
        parser.error("Candidate wheel/version/SHA-256 must be supplied together")
    redis_url = validate_redis_url(args.redis_url)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cache-network-bench-") as tmp:
        root = Path(tmp)
        venv.EnvBuilder(with_pip=True).create(str(root / "venv"))
        python = _venv_python(root / "venv")
        dist = root / "wheel"
        dist.mkdir()
        selected_version = VERSION
        source = "published PyPI 0.6.0 SHA-verified wheel"
        if args.candidate_wheel is not None:
            selected_version = args.candidate_version
            candidate = args.candidate_wheel.resolve()
            verify_candidate_wheel(
                candidate, selected_version, args.candidate_sha256
            )
            shutil.copyfile(candidate, dist / candidate.name)
            # Verify again after the copy: the installed bytes are the reviewed bytes.
            verify_candidate_wheel(
                dist / candidate.name, selected_version, args.candidate_sha256
            )
            source = "local candidate wheel, expected SHA-256 verified"
        else:
            _run([
                str(python), "-m", "pip", "download", "--disable-pip-version-check",
                "--no-cache-dir", "--no-deps", "--only-binary=:all:",
                "--dest", str(dist), f"{PACKAGE}=={VERSION}",
            ], root)
        wheels = list(dist.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected exactly one wheel")
        sha = hashlib.sha256(wheels[0].read_bytes()).hexdigest()
        if args.candidate_wheel is None and sha != WHEEL_SHA256:
            raise RuntimeError("Published wheel SHA mismatch")
        _run([
            str(python), "-m", "pip", "install", "--disable-pip-version-check",
            "--no-cache-dir", str(wheels[0]), *FRAMEWORK, UVICORN,
        ], root)
        _run([str(python), "-m", "pip", "check"], root)
        freeze = _run([str(python), "-m", "pip", "freeze"], root)
        (output / "pip-freeze.txt").write_text(freeze, encoding="utf-8")
        provenance = {
            "profile": "real-loopback-HTTP-socket",
            "wheel_version": selected_version,
            "wheel_source": source,
            "wheel_filename": wheels[0].name,
            "wheel_sha256": sha,
            "framework_pins": list(FRAMEWORK),
            "http_server": UVICORN,
            "repeats": args.repeats,
            "samples_per_case_per_run": args.iterations,
            "isolated_python": "3.12",
            "workflow_trigger_sha": os.environ.get("GITHUB_SHA", "local-unrecorded"),
            "checkout_sha": os.environ.get("BENCHMARK_CHECKOUT_SHA", "local-unrecorded"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "local-unrecorded"),
            "scope": "description only; shared CI runner is not independent hardware",
        }
        (output / "provenance.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        for index in range(args.repeats):
            destination = output if index == 0 else output / "runs" / f"run-{index + 1:02d}"
            destination.mkdir(parents=True, exist_ok=True)
            _run([
                str(python), "-I", str(WORKLOAD), "run",
                "--iterations", str(args.iterations),
                "--redis-url", redis_url, "--output", str(destination),
                "--expected-version", selected_version,
            ], root)
        aggregate_results(output, args.repeats)
    print("Verified selected wheel and real 127.0.0.1 socket HTTP; no release action")


if __name__ == "__main__":
    main()

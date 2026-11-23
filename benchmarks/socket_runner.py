"""Run the real TCP socket HTTP profile on a SHA-verified published wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import venv
from pathlib import Path

from aggregate import aggregate_results
from runner import FRAMEWORK, PACKAGE, VERSION, WHEEL_SHA256, _run, _venv_python, validate_redis_url

WORKLOAD = Path(__file__).with_name("socket_workload.py").resolve()
UVICORN = "uvicorn==0.34.2"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--redis-url", default="redis://127.0.0.1:6379/15")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=120)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("This profile uses CPython 3.12")
    if not 1 <= args.repeats <= 3:
        parser.error("Repeats must be 1..3 isolated workload processes")
    if not 100 <= args.iterations <= 1000:
        parser.error("Iterations must be 100..1000 for each latency case")
    redis_url = validate_redis_url(args.redis_url)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cache-network-bench-") as tmp:
        root = Path(tmp)
        venv.EnvBuilder(with_pip=True).create(str(root / "venv"))
        python = _venv_python(root / "venv")
        dist = root / "wheel"
        dist.mkdir()
        _run([
            str(python), "-m", "pip", "download", "--disable-pip-version-check",
            "--no-cache-dir", "--no-deps", "--only-binary=:all:",
            "--dest", str(dist), f"{PACKAGE}=={VERSION}",
        ], root)
        wheels = list(dist.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected one published wheel")
        sha = hashlib.sha256(wheels[0].read_bytes()).hexdigest()
        if sha != WHEEL_SHA256:
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
            "wheel_version": VERSION,
            "wheel_filename": wheels[0].name,
            "wheel_sha256": sha,
            "framework_pins": list(FRAMEWORK),
            "http_server": UVICORN,
            "repeats": args.repeats,
            "samples_per_case_per_run": args.iterations,
            "isolated_python": "3.12",
            "source_sha": os.environ.get("GITHUB_SHA", "local-unrecorded"),
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
            ], root)
        aggregate_results(output, args.repeats)
    print("Verified published wheel and real 127.0.0.1 socket HTTP; no release action")


if __name__ == "__main__":
    main()

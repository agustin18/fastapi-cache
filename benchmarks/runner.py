"""Run benchmark workloads with the immutable published 0.6.0 wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from urllib.parse import urlsplit

PACKAGE = "fastapi-cache-stable"
VERSION = "0.6.0"
WHEEL_SHA256 = "60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e"
FRAMEWORK = ("fastapi==0.115.12", "pydantic==2.8.2", "httpx==0.27.0", "redis==5.2.1")
WORKLOAD = Path(__file__).with_name("workload.py").resolve()


def validate_redis_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "redis"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.path != "/15"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.port is None
    ):
        raise ValueError("Benchmark Redis must be loopback redis://host:port/15 without credentials")
    return value


def _run(argv: list[str], cwd: Path) -> str:
    try:
        completed = subprocess.run(  # noqa: S603 - controlled interpreter and fixed arguments
            argv, cwd=str(cwd), text=True, check=True, capture_output=True
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Isolated benchmark command failed:\n" + error.stdout + "\n" + error.stderr
        ) from error
    return completed.stdout


def _venv_python(folder: Path) -> Path:
    if sys.platform == "win32":
        return folder / "Scripts" / "python.exe"
    return folder / "bin" / "python"


def main() -> None:
    # Executable script has benchmarks/ on sys.path; module import in tests does not.
    from aggregate import aggregate_results

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--redis-url", default="redis://127.0.0.1:6379/15")
    parser.add_argument("--repeats", type=int, default=None,
                        help="Fresh workload processes (default: smoke=1, full=3; max 5)")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Reproducibility requires CPython 3.12 for this benchmark profile")
    url = validate_redis_url(args.redis_url)
    repeats = args.repeats if args.repeats is not None else (3 if args.profile == "full" else 1)
    if not 1 <= repeats <= 5:
        parser.error("--repeats must be between 1 and 5")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cache-published-bench-") as tmp:
        root = Path(tmp)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(str(environment))
        python = _venv_python(environment)
        download = root / "wheel"
        download.mkdir()
        _run([str(python), "-m", "pip", "download", "--disable-pip-version-check",
              "--no-cache-dir", "--no-deps", "--only-binary=:all:",
              "--dest", str(download), f"{PACKAGE}=={VERSION}"], root)
        wheels = sorted(download.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected exactly one published wheel")
        digest = hashlib.sha256(wheels[0].read_bytes()).hexdigest()
        if digest != WHEEL_SHA256:
            raise RuntimeError(f"Wheel SHA-256 mismatch: {digest}")
        _run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
              "--no-cache-dir", str(wheels[0]), *FRAMEWORK], root)
        _run([str(python), "-m", "pip", "check"], root)
        freeze = _run([str(python), "-m", "pip", "freeze"], root)
        (output / "pip-freeze.txt").write_text(freeze, encoding="utf-8")
        provenance = {
            "benchmark_scope": "published-wheel-only",
            "package": PACKAGE,
            "published_version": VERSION,
            "wheel_filename": wheels[0].name,
            "wheel_sha256": digest,
            "framework_pins": list(FRAMEWORK),
            "profile": args.profile,
            "repeats": repeats,
            "python": sys.version.split()[0],
            "workflow_source_sha": os.environ.get("GITHUB_SHA", "local-unrecorded"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "local-unrecorded"),
        }
        (output / "provenance.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        for index in range(repeats):
            destination = (output if index == 0 else output / "runs" / f"run-{index + 1:02d}")
            destination.mkdir(parents=True, exist_ok=True)
            print(f"Running {args.profile} iteration {index + 1}/{repeats}", flush=True)
            _run([str(python), "-I", str(WORKLOAD), "--profile", args.profile,
                  "--output", str(destination), "--redis-url", url], root)
        result = aggregate_results(output, repeats)
        print(f"Completed {repeats} isolated workload process(es), "
              f"{len(result['cases'])} comparable cases; aggregate.json written")
    print("Published wheel SHA-256 verified; isolated benchmark environment removed")


if __name__ == "__main__":
    main()

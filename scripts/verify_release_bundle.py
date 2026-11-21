"""Fail-closed validation of a reviewed release bundle; never build or publish."""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

WORKFLOW = ".github/workflows/migration-candidate-phase-b.yml"
PACKAGE = "fastapi-cache-stable"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_run(
    run: Dict[str, Any], repository: str, source_sha: str, run_id: str
) -> None:
    require(str(run.get("id")) == run_id, "unexpected workflow run id")
    require(
        run.get("head_repository", {}).get("full_name") == repository,
        "workflow must belong to this repository",
    )
    require(run.get("head_sha") == source_sha, "run source SHA mismatch")
    require(run.get("head_branch") == "stable", "run must be on stable")
    require(run.get("event") == "workflow_dispatch", "manual final run required")
    require(run.get("path") in (WORKFLOW, WORKFLOW + "@refs/heads/stable"),
            "wrong evidence workflow")
    require(run.get("status") == "completed", "evidence run is incomplete")
    require(run.get("conclusion") == "success", "evidence run did not pass")


def verify_bundle(
    bundle: Path,
    run: Dict[str, Any],
    source_sha: str,
    version: str,
    wheel_hash: str,
    sdist_hash: str,
) -> Dict[str, str]:
    require(re.fullmatch(r"[0-9a-f]{64}", wheel_hash) is not None, "invalid wheel hash")
    require(re.fullmatch(r"[0-9a-f]{64}", sdist_hash) is not None, "invalid sdist hash")
    provenance = json.loads((bundle / "provenance.json").read_text())
    require(provenance["source_sha"] == source_sha, "bundle source SHA mismatch")
    require(str(provenance["workflow_run_id"]) == str(run["id"]), "bundle run mismatch")
    require(str(provenance["workflow_attempt"]) == str(run["run_attempt"]),
            "bundle attempt mismatch; rerun ALL evidence jobs")
    require(provenance["candidate_version"] == version, "bundle version mismatch")
    require(provenance["published"] is False, "expected unpublished evidence bundle")
    wheel = provenance["wheel"]
    sdist = provenance["sdist"]
    require(
        isinstance(wheel, str)
        and re.fullmatch(
            r"fastapi_cache_stable-" + re.escape(version) + r"-[A-Za-z0-9_.-]+\.whl",
            wheel,
        ) is not None,
        "unexpected wheel name",
    )
    require(sdist == f"fastapi_cache_stable-{version}.tar.gz", "unexpected sdist name")
    expected = {wheel: wheel_hash, sdist: sdist_hash}
    require(
        {p.name for p in bundle.iterdir()} == set(expected) | {"SHA256SUMS", "provenance.json"},
        "unexpected evidence bundle contents",
    )
    manifest = (bundle / "SHA256SUMS").read_text().splitlines()
    require(
        len(manifest) == 2
        and set(manifest) == {f"{digest}  {name}" for name, digest in expected.items()},
        "manifest does not match explicitly approved hashes",
    )
    for name, digest in expected.items():
        path = bundle / name
        require(path.is_file() and not path.is_symlink(), "invalid artifact file")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                f"artifact hash mismatch: {name}")
    return expected


def verify_test_index(version: str, expected: Dict[str, str]) -> None:
    # Only a fixed, trusted index host; no credentials or URLs from input.
    url = f"https://test.pypi.org/pypi/{PACKAGE}/{version}/json"
    with urlopen(url, timeout=30) as response:  # noqa: S310
        payload = json.load(response)
    require(payload["info"]["version"] == version, "wrong TestPyPI version")
    actual = {
        item["filename"]: item["digests"]["sha256"]
        for item in payload["urls"]
    }
    require(actual == expected, "TestPyPI distributions differ from approved bundle")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-json", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--wheel-sha", required=True)
    parser.add_argument("--sdist-sha", required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-testpypi", action="store_true")
    args = parser.parse_args()
    require(re.fullmatch(r"[0-9]+", args.run_id) is not None, "invalid run id")
    require(re.fullmatch(r"[0-9a-f]{40}", args.source_sha) is not None, "invalid source SHA")
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version) is not None,
            "expected final release version")
    run = json.loads(args.run_json.read_text())
    validate_run(run, args.repository, args.source_sha, args.run_id)
    expected = verify_bundle(
        args.bundle, run, args.source_sha, args.version, args.wheel_sha, args.sdist_sha
    )
    if args.require_testpypi:
        verify_test_index(args.version, expected)
    args.output.mkdir()
    for name in expected:
        shutil.copyfile(args.bundle / name, args.output / name)
    print(json.dumps({"source_sha": args.source_sha, "run_id": args.run_id,
                      "artifact_sha256": expected}, sort_keys=True))


if __name__ == "__main__":
    main()

# ruff: noqa: S101 - comparison deliberately asserts migration safety
"""Fail-closed before/after comparison of two isolated demo executions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def verify(legacy: dict[str, Any], replacement: dict[str, Any]) -> None:
    assert (legacy["distribution"], legacy["version"]) == (
        "fastapi-cache2",
        "0.2.2",
    )
    assert (replacement["distribution"], replacement["version"]) == (
        "fastapi-cache-stable",
        "0.5.0",
    )

    for report in (legacy, replacement):
        assert report["public_statuses"] == ["MISS", "HIT"]
        assert report["conditional_status"] == 304

    # Published upstream deliberately exhibits the bug in this isolated,
    # fictional demonstration. This is not behavior to preserve in production.
    assert legacy["viewer_statuses"] == ["MISS", "HIT"]
    assert legacy["viewer_results"] == ["alice", "alice"]

    # The published fork bypasses auth-derived results by default.
    assert replacement["viewer_statuses"] == [None, None]
    assert replacement["viewer_results"] == ["alice", "bob"]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: compare.py legacy.json replacement.json")
    legacy = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    replacement = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    verify(legacy, replacement)
    print("PASS: unchanged FastAPI imports, ordinary MISS -> HIT, ETag 304")
    print("PASS: legacy private-data reuse reproduced with fictional identities")
    print("PASS: published 0.5.0 bypasses protected requests by default")
    print("NOTE: this is not evidence of safe rollback for authenticated data")


if __name__ == "__main__":
    main()

"""Classify PR file diffs for the Towncrier gate, failing closed for code.

A docs-only change should not need a news fragment. Every non-documentation
path still requires the normal Towncrier policy (unless the PR explicitly
carries the audited skip-changelog label). Run with a full git fetch.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import PurePosixPath
from typing import Iterable, List


def is_docs_only(paths: Iterable[str]) -> bool:
    """Only a nonempty list consisting exclusively of Markdown/RST is exempt."""
    changed = list(paths)
    return bool(changed) and all(
        PurePosixPath(path).suffix.lower() in {".md", ".rst"}
        for path in changed
    )


def list_changed_paths(base: str = "origin/stable") -> List[str]:
    # --no-renames keeps *both* sides of a rename in view, so renaming
    # Python/workflow files to Markdown cannot accidentally bypass the gate.
    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", f"{base}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/stable")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    changed = list_changed_paths(base=args.base)
    docs_only = is_docs_only(changed)
    print("Changed paths considered by Towncrier:")
    for path in changed:
        print(f" - {path}")
    print(f"Markdown/RST-only: {docs_only}")

    # GitHub Actions output is written only after the full classifier succeeds.
    with open(args.output, "a", encoding="utf-8") as output:
        output.write(f"docs_only={str(docs_only).lower()}\n")


if __name__ == "__main__":
    main()

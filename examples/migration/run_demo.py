"""Cross-platform single-command before/after migration demo.

Creates two disposable virtual environments; never installs both packages
into one interpreter or touches Redis, credentials or production data.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


FRAMEWORK = ("fastapi==0.111.1", "pydantic==2.8.2", "httpx==0.27.0")
PROVIDERS = {
    "legacy": "fastapi-cache2==0.2.2",
    "replacement": "fastapi-cache-stable==0.5.0",
}
DIRECTORY = Path(__file__).resolve().parent


def _python_in_venv(folder: Path) -> Path:
    if sys.platform == "win32":
        return folder / "Scripts" / "python.exe"
    return folder / "bin" / "python"


def _run(executable: Path, args: list[str], cwd: Path) -> str:
    completed = subprocess.run(  # noqa: S603 - trusted local venv interpreter and fixed args
        [str(executable), *args],
        cwd=str(cwd),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return completed.stdout


def _probe(root: Path, mode: str) -> dict[str, object]:
    environment = root / mode
    venv.EnvBuilder(with_pip=True).create(str(environment))
    python = _python_in_venv(environment)
    print(f"Installing isolated {PROVIDERS[mode]} ...", flush=True)
    _run(
        python,
        [
            "-m", "pip", "install", "--disable-pip-version-check",
            PROVIDERS[mode], *FRAMEWORK,
        ],
        root,
    )
    _run(python, ["-m", "pip", "check"], root)
    output = _run(python, ["-I", str(DIRECTORY / "app.py"), mode], root)
    report: dict[str, object] = json.loads(output)
    (root / f"{mode}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    if sys.version_info[:2] not in {(3, 11), (3, 12)}:
        raise SystemExit(
            "This pinned demonstration was verified on CPython 3.11/3.12. "
            "Use one of those versions; this is not a library support limit."
        )
    with tempfile.TemporaryDirectory(prefix="fastapi-cache-demo-") as temp:
        root = Path(temp)
        for mode in ("legacy", "replacement"):
            _probe(root, mode)
        print(
            _run(
                Path(sys.executable),
                [
                    "-I",
                    str(DIRECTORY / "compare.py"),
                    str(root / "legacy.json"),
                    str(root / "replacement.json"),
                ],
                root,
            ),
            end="",
        )
    print("Temporary environments deleted; host environment unchanged.")


if __name__ == "__main__":
    main()

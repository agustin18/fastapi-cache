"""Fail-closed local candidate identity for isolated socket benchmarks.

This verifies metadata and integrity; it does not approve the source, wheel,
dependencies, performance or release. A real release needs independent review.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from email.parser import Parser
from pathlib import Path


def verify_candidate_wheel(path: Path, version: str, expected_sha256: str) -> str:
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.dev[0-9]+)?", version) is None:
        raise ValueError("Candidate version must be X.Y.Z or X.Y.Z.devN")
    if version == "0.6.0":
        raise ValueError("Use the immutable published baseline path for 0.6.0")
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise ValueError("Expected a lowercase 64-character SHA-256 digest")
    if path.name != f"fastapi_cache_stable-{version}-py3-none-any.whl":
        raise ValueError("Wrong candidate wheel filename or tag")
    if not path.is_file():
        raise ValueError("Candidate wheel file is missing")

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Candidate wheel SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        meta_path = f"fastapi_cache_stable-{version}.dist-info/METADATA"
        if archive.namelist().count(meta_path) != 1:
            raise ValueError("Candidate wheel metadata path missing or duplicated")
        info = Parser().parsestr(archive.read(meta_path).decode("utf-8"))
        if info.get("Name") != "fastapi-cache-stable":
            raise ValueError("Wrong candidate distribution identity")
        if info.get("Version") != version:
            raise ValueError("Candidate metadata version mismatch")
    return digest

"""Version identity for the C4 comparison; no runtime dependencies."""

from typing import Optional

BASELINE_VERSION = "0.7.2"
CANDIDATE_MODES = ("candidate-legacy", "scoped-off", "scoped-on")


def expected_distribution_version(mode: str, candidate_version: Optional[str] = None) -> str:
    """Return the installed version required for a preregistered C4 mode."""
    if mode == "published":
        return BASELINE_VERSION
    if mode not in CANDIDATE_MODES:
        raise ValueError("Unknown benchmark mode: " + mode)
    if not candidate_version:
        raise ValueError("Candidate benchmark modes require an expected version")
    return candidate_version

"""Version identity for the C4 comparison; no runtime dependencies."""

from typing import Optional

BASELINE_VERSION = "0.7.2"  # historical CLI default for reproducibility
BASELINE_VERSIONS = ("0.7.2", "0.8.0")
PROFILES = {"full": (120, 20, 4), "smoke": (24, 4, 1)}
CANDIDATE_MODES = ("candidate-legacy", "scoped-off", "scoped-on")


def expected_distribution_version(
    mode: str, candidate_version: Optional[str] = None,
    baseline_version: str = BASELINE_VERSION,
) -> str:
    """Return the installed version required for a preregistered C4 mode."""
    if baseline_version not in BASELINE_VERSIONS:
        raise ValueError("Unsupported baseline version")
    if mode == "published":
        return baseline_version
    if mode not in CANDIDATE_MODES:
        raise ValueError("Unknown benchmark mode: " + mode)
    if not candidate_version:
        raise ValueError("Candidate benchmark modes require an expected version")
    return candidate_version

"""Keep technical release criteria independent of adoption quotas."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_policy_has_no_external_consumer_gate() -> None:
    policy = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "No minimum number of external consumers" in policy
    assert "explicit maintainer approval" in policy
    for path in (
        "docs/releases/RELEASE_CANDIDATE_0.6.0.md",
        "docs/releases/RELEASE_NOTES_0.6.0.md",
        "ROADMAP.md",
        "site_docs/roadmap.md",
    ):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "0/2" not in text, path
        assert "#91 consumer" not in text, path
        assert "two real consumer validations" not in text.lower(), path


def test_release_policy_retains_technical_checks() -> None:
    candidate = (
        ROOT / "docs/releases/RELEASE_CANDIDATE_0.6.0.md"
    ).read_text(encoding="utf-8")
    for requirement in (
        "SHA-256",
        "Dependabot",
        "#53",
        "seven exact-bundle security profiles",
        "TestPyPI",
        "maintainer GO",
        "NOT AUTHORIZED",
    ):
        assert requirement in candidate

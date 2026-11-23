"""Ensure Redis fault qualification cannot accidentally target a shared server."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_disposable_server_and_installed_wheel_gate() -> None:
    source = (ROOT / "tests/redis_fault_probe.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/redis-fault-070.yml").read_text(
        encoding="utf-8"
    )
    for token in (
        'f"127.0.0.1:{port}:6379"',
        '"redis:7.4"',
        'REDIS_FAULT_DISPOSABLE',
        '"stop", "--time", "1"',
        '"start", name',
        '"rm", "-f", name',
        '"--save", ""',
        '"site-packages"',
        "await client.aclose()",
    ):
        assert token in source, token
    for forbidden in ("flushdb(", "flushall(", "redis://", "docker kill"):
        assert forbidden not in source.lower(), forbidden
    assert 'python -I "$GITHUB_WORKSPACE/tests/redis_fault_probe.py"' in workflow
    assert 'REDIS_FAULT_DISPOSABLE: "1"' in workflow
    assert "docker pull redis:7.4" in workflow
    assert 'python: "3.8"' in workflow
    assert 'python: "3.12"' in workflow
    assert 'python: "3.13"' in workflow

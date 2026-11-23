"""Regression contract for the real socket published-wheel profile (#100)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_real_http_uses_verified_published_wheel_not_checkout() -> None:
    runner = (ROOT / "benchmarks/socket_runner.py").read_text(encoding="utf-8")
    workload = (ROOT / "benchmarks/socket_workload.py").read_text(encoding="utf-8")
    assert "WHEEL_SHA256" in runner
    assert "sha != WHEEL_SHA256" in runner
    assert "pip" in runner and '"-I"' in runner
    assert '"site-packages" not in imported.parts' in workload
    assert 'metadata.version("fastapi-cache-stable") != "0.6.0"' in workload
    assert "ASGITransport" not in workload
    assert "uvicorn.Server" in workload
    assert 'host="127.0.0.1"' in workload
    assert 'base_url=f"http://127.0.0.1:{port}"' in workload
    assert "socket.AF_INET" in workload


def test_no_external_redis_or_global_deletion_in_socket_profile() -> None:
    script = (ROOT / "benchmarks/socket_workload.py").read_text(encoding="utf-8")
    runner = (ROOT / "benchmarks/socket_runner.py").read_text(encoding="utf-8")
    assert "validate_redis_url(args.redis_url)" in runner
    assert 'p.path != "/15"' in script
    assert 'p.hostname not in ("localhost", "127.0.0.1", "::1")' in script
    assert "FLUSHDB(" not in script
    assert "flushdb(" not in script
    assert "flushall(" not in script
    assert 'scan_iter(match=prefix + ":*")' in script
    assert "redis.unlink(*keys[" in script
    assert '"perf-http-" + uuid.uuid4().hex' in script


def test_network_profile_is_separate_but_manual_and_pr_executable() -> None:
    text = (ROOT / ".github/workflows/benchmark-published.yml").read_text(
        encoding="utf-8"
    )
    docs = (ROOT / "benchmarks/README.md").read_text(encoding="utf-8")
    assert "  workflow_dispatch:\n" in text
    assert text.count("\n  socket-http:\n") == 1
    portion = text.split("\n  socket-http:\n", 1)[1]
    assert "python benchmarks/socket_runner.py --repeats 2" in portion
    assert "redis:7.4" in portion
    assert "if: github.event_name" not in portion
    assert "Real loopback HTTP socket profile" in docs
    assert "#100 remains OPEN" in docs

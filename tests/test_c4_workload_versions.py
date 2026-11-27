"""C4 version identity must separate the fixed baseline from the candidate."""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load() -> ModuleType:
    path = ROOT / "benchmarks" / "c4_versions.py"
    spec = importlib.util.spec_from_file_location("c4_versions", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_published_mode_remains_pinned_to_the_baseline() -> None:
    module = _load()
    assert module.BASELINE_VERSION == "0.7.2"
    assert module.expected_distribution_version("published") == "0.7.2"
    assert module.expected_distribution_version("published", "0.8.0") == "0.7.2"


@pytest.mark.parametrize("mode", ["candidate-legacy", "scoped-off", "scoped-on"])
def test_candidate_modes_use_the_exact_candidate_version(mode: str) -> None:
    module = _load()
    assert module.expected_distribution_version(mode, "0.8.0") == "0.8.0"


def test_candidate_modes_require_an_expected_version() -> None:
    module = _load()
    with pytest.raises(ValueError, match="require an expected version"):
        module.expected_distribution_version("candidate-legacy")


def test_unknown_mode_is_rejected() -> None:
    module = _load()
    with pytest.raises(ValueError, match="Unknown benchmark mode"):
        module.expected_distribution_version("unknown", "0.8.0")


def test_workflow_passes_candidate_version_and_loads_helper() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/c4-performance.yml").read_text(encoding="utf-8")
    assert "benchmarks/c4_versions.py" in workflow
    assert '--candidate-version "$candidate_version"' in workflow
    assert "scripts/release_contract.py version" in workflow
    source = (root / "benchmarks/c4_workload.py").read_text(encoding="utf-8")
    assert 'metadata.version("fastapi-cache-stable") == "0.7.2"' not in source


def test_active_baseline_and_profiles() -> None:
    module = _load()
    assert module.expected_distribution_version("published", "0.8.0", "0.8.0") == "0.8.0"
    assert module.expected_distribution_version("candidate-legacy", "0.9.0", "0.8.0") == "0.9.0"
    with pytest.raises(ValueError, match="Unsupported baseline"):
        module.expected_distribution_version("published", baseline_version="0.9.0")
    assert module.PROFILES == {"full": (120, 20, 4), "smoke": (24, 4, 1)}


def test_isolation_and_performance_triggers_are_separate() -> None:
    isolation = (ROOT / ".github/workflows/c4-evidence.yml").read_text(encoding="utf-8")
    performance = (ROOT / ".github/workflows/c4-performance.yml").read_text(encoding="utf-8")
    assert "  performance:" not in isolation
    assert "  isolation:" in isolation
    assert '"fastapi_cache/**"' in isolation
    assert '"3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"' in isolation
    assert "inputs.profile || 'smoke'" in performance
    assert "inputs.baseline || '0.8.0'" in performance
    assert "workflow_dispatch:" in performance
    assert "default: full" in performance
    assert "smoke) rounds=1" in performance
    assert "full) rounds=4" in performance
    assert "31257d8de8e5b36b13f50d233c72bf3a53d99b8eb3376264112be9072abf5fa0" in performance
    assert "4a7d200744424f88bfaee2a4b1fc6958e138aa86236c1906964d3cda41861bd1" in performance


def _load_aggregate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("c4_aggregate", ROOT / "benchmarks/c4_aggregate.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture(root: Path, profile: str, baseline: str, historical: bool = False) -> None:
    samples, _, rounds = _load().PROFILES[profile]
    for i in range(rounds):
        for mode in ("published", "candidate-legacy", "scoped-off", "scoped-on"):
            directory = root / f"round-{i + 1}" / mode
            directory.mkdir(parents=True)
            case = {"samples": samples, "p50_ms": 1.0, "requests_per_second": 100.0}
            if profile == "full":
                case.update(p95_ms=2.0, p99_ms=3.0)
            summary: Dict[str, Any] = {
                "mode": mode, "cases": {"example": case},
                "cpu_seconds": 1, "wall_seconds": 2, "peak_process_rss_kib": 3,
                "lifecycle": {},
            }
            if not historical:
                summary.update(profile=profile, baseline_version=baseline)
            (directory / "summary.json").write_text(json.dumps(summary), encoding="utf-8")


@pytest.mark.parametrize(("profile", "baseline", "historical"), [
    ("full", "0.7.2", True), ("full", "0.8.0", False), ("smoke", "0.8.0", False),
])
def test_aggregate_profile_contract(tmp_path: Path, profile: str, baseline: str, historical: bool) -> None:
    _fixture(tmp_path, profile, baseline, historical)
    result = _load_aggregate().aggregate(tmp_path, profile, baseline)
    assert result["profile"] == profile
    assert result["baseline_version"] == baseline
    comparison = result["cases"]["example"]["published_to_candidate-legacy"]
    if profile == "full":
        assert len(result["order"]) == 4
        assert comparison["p99_ms"]["ratio_stdev"] == 0
    else:
        assert len(result["order"]) == 1
        assert set(comparison) == {"p50_ms", "requests_per_second"}
        assert comparison["p50_ms"]["ratio_stdev"] is None
        assert result["schema"] == "c4-smoke-v1"


def test_aggregate_rejects_mixed_profile_baseline_and_samples(tmp_path: Path) -> None:
    _fixture(tmp_path, "smoke", "0.8.0")
    module = _load_aggregate()
    with pytest.raises(ValueError, match="Mismatched comparison"):
        module.aggregate(tmp_path, "smoke", "0.7.2")
    path = tmp_path / "round-1/published/summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["cases"]["example"]["samples"] = 23
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Insufficient samples"):
        module.aggregate(tmp_path, "smoke", "0.8.0")

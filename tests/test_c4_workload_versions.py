"""C4 version identity must separate the fixed baseline from the candidate."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

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
    workflow = (root / ".github/workflows/c4-evidence.yml").read_text(encoding="utf-8")
    assert "benchmarks/c4_versions.py" in workflow
    assert '--candidate-version "$candidate_version"' in workflow
    assert "scripts/release_contract.py version" in workflow
    source = (root / "benchmarks/c4_workload.py").read_text(encoding="utf-8")
    assert 'metadata.version("fastapi-cache-stable") == "0.7.2"' not in source

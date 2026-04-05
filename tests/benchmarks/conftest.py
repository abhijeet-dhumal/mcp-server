"""Benchmark test configuration and utilities."""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Benchmark modules are not bound by the unit-suite default timeout."""
    for item in items:
        if "/benchmarks/" in item.nodeid or "\\benchmarks\\" in item.nodeid:
            item.add_marker(pytest.mark.timeout(0))

RESULTS_DIR = Path(__file__).parent / "results"


def get_commit_hash() -> str:
    """Get current git commit hash."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


@pytest.fixture(scope="session")
def benchmark_metadata():
    """Metadata for benchmark results."""
    return {
        "commit": get_commit_hash(),
        "timestamp": datetime.now().isoformat(),
        "python_version": os.sys.version.split()[0],
    }


@pytest.fixture(scope="session")
def results_dir():
    """Ensure results directory exists."""
    RESULTS_DIR.mkdir(exist_ok=True)
    return RESULTS_DIR


def save_benchmark_results(results: dict, name: str, results_dir: Path):
    """Save benchmark results to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    commit = get_commit_hash()
    filename = f"{name}_{timestamp}_{commit}.json"
    filepath = results_dir / filename

    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)

    return filepath

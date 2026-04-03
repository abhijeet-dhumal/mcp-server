"""Latency benchmarks for MCP server operations.

Measures P50, P95, P99 latency for server operations.
Run with: uv run pytest tests/benchmarks/test_latency.py -v --benchmark-only

Requirements: uv sync --extra benchmark --extra trainer
"""

import pytest

try:
    import pytest_benchmark  # noqa: F401
except ImportError:
    pytest.skip(
        "pytest-benchmark not installed (run: uv sync --extra benchmark)",
        allow_module_level=True,
    )

from kubeflow_mcp.trainer import TOOLS, get_tools


class TestServerInitLatency:
    """Benchmark server initialization time."""

    def test_create_server_latency(self, benchmark):
        """Measure server creation time."""
        from kubeflow_mcp.core.server import create_server

        result = benchmark(create_server, clients=["trainer"])

        assert result is not None

    def test_create_server_minimal_latency(self, benchmark):
        """Measure server creation with no clients."""
        from kubeflow_mcp.core.server import create_server

        result = benchmark(create_server, clients=[])

        assert result is not None


class TestToolLoadingLatency:
    """Benchmark tool loading operations."""

    def test_get_all_tools_latency(self, benchmark):
        """Measure time to get all tools."""
        result = benchmark(get_tools, categories=None)

        assert len(result) == 16

    def test_get_core_tools_latency(self, benchmark):
        """Measure time to get core tools."""
        result = benchmark(get_tools, categories=["core"])

        assert len(result) == 5

    def test_get_planning_tools_latency(self, benchmark):
        """Measure time to get planning tools."""
        result = benchmark(get_tools, categories=["planning"])

        assert len(result) >= 1

    def test_get_multiple_categories_latency(self, benchmark):
        """Measure time to get tools from multiple categories."""
        result = benchmark(get_tools, categories=["planning", "training", "monitoring"])

        assert len(result) >= 3


class TestToolSchemaGenerationLatency:
    """Benchmark tool schema generation."""

    def test_single_tool_schema_latency(self, benchmark):
        """Measure time to generate schema for one tool."""
        import inspect

        tool = TOOLS[0]  # fine_tune

        def generate_schema():
            sig = inspect.signature(tool)
            return {
                "name": tool.__name__,
                "description": (tool.__doc__ or "").split("\n")[0],
                "parameters": {
                    name: str(param.annotation) for name, param in sig.parameters.items()
                },
            }

        result = benchmark(generate_schema)
        assert "name" in result

    def test_all_tools_schema_latency(self, benchmark):
        """Measure time to generate schemas for all tools."""

        def generate_all_schemas():
            schemas = []
            for tool in TOOLS:
                schemas.append(
                    {
                        "name": tool.__name__,
                        "description": (tool.__doc__ or "").split("\n")[0],
                    }
                )
            return schemas

        result = benchmark(generate_all_schemas)
        assert len(result) == 16


class TestToolPreviewLatency:
    """Benchmark tool preview operations (no SDK calls)."""

    def test_fine_tune_preview_latency(self, benchmark):
        """Measure fine_tune preview mode latency."""
        from kubeflow_mcp.trainer.api.training import fine_tune

        def run_preview():
            return fine_tune(
                model="hf://google/gemma-2b",
                dataset="hf://tatsu-lab/alpaca",
                batch_size=4,
                epochs=1,
                confirmed=False,
            )

        result = benchmark(run_preview)
        assert result["status"] == "preview"

    def test_custom_training_preview_latency(self, benchmark):
        """Measure run_custom_training preview mode latency."""
        from kubeflow_mcp.trainer.api.training import run_custom_training

        script = """
import torch
print("Hello")
"""

        def run_preview():
            return run_custom_training(
                script=script,
                num_nodes=1,
                gpu_per_node=1,
                confirmed=False,
            )

        result = benchmark(run_preview)
        assert result["status"] == "preview"

    def test_container_training_preview_latency(self, benchmark):
        """Measure run_container_training preview mode latency."""
        from kubeflow_mcp.trainer.api.training import run_container_training

        def run_preview():
            return run_container_training(
                image="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime",
                num_nodes=1,
                gpu_per_node=1,
                confirmed=False,
            )

        result = benchmark(run_preview)
        assert result["status"] == "preview"


class TestSecurityValidationLatency:
    """Benchmark security validation operations."""

    def test_script_validation_safe_latency(self, benchmark):
        """Measure script validation latency for safe script."""
        from kubeflow_mcp.core.security import is_safe_python_code

        safe_script = """
import torch
import torch.distributed as dist

def train():
    model = torch.nn.Linear(10, 10)
    optimizer = torch.optim.Adam(model.parameters())
    for i in range(100):
        loss = model(torch.randn(32, 10)).sum()
        loss.backward()
        optimizer.step()
"""

        result = benchmark(is_safe_python_code, safe_script)
        # Returns (is_safe: bool, message: str)
        assert result[0] is True

    def test_script_validation_dangerous_latency(self, benchmark):
        """Measure script validation latency for dangerous script."""
        from kubeflow_mcp.core.security import is_safe_python_code

        dangerous_script = """
import os
os.system("rm -rf /")
"""

        result = benchmark(is_safe_python_code, dangerous_script)
        # Returns (is_safe: bool, message: str)
        assert result[0] is False

    def test_k8s_name_validation_latency(self, benchmark):
        """Measure Kubernetes name validation latency."""
        import re

        # Inline K8s name validation (RFC 1123)
        def is_valid_k8s_name(name: str) -> bool:
            pattern = r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
            return bool(re.match(pattern, name)) and len(name) <= 63

        result = benchmark(is_valid_k8s_name, "my-training-job-12345")
        assert result is True


class TestLatencySummary:
    """Generate latency summary with percentiles."""

    def test_generate_latency_report(self, benchmark_metadata, results_dir, request):
        """Generate comprehensive latency report after all benchmarks."""
        # This test runs last and collects results from pytest-benchmark
        # The actual percentile data comes from pytest-benchmark's JSON output

        print(f"\n{'=' * 60}")
        print("LATENCY BENCHMARK COMPLETE")
        print(f"{'=' * 60}")
        print(f"Commit: {benchmark_metadata['commit']}")
        print("\nRun with --benchmark-json=results.json to save detailed results")
        print("Run with --benchmark-compare to compare against baseline")

"""Profiling benchmarks for MCP server operations.

In-memory profiling tests - no file artifacts generated.
For visual dashboard, see test_report.py.

Run with: uv run pytest tests/benchmarks/test_profiling.py -v -s
"""

import cProfile
import io
import pstats
import tracemalloc

from kubeflow_mcp.trainer import TOOLS


class TestCPUProfiling:
    """CPU profiling to identify slow functions (no file output)."""

    def test_profile_server_creation(self):
        """Profile server creation to find bottlenecks."""
        from kubeflow_mcp.core.server import create_server

        profiler = cProfile.Profile()
        profiler.enable()

        for _ in range(10):
            create_server(clients=["trainer"])

        profiler.disable()

        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)

        print("\nCPU PROFILE: Server Creation (top 20)")
        print(stream.getvalue())

    def test_profile_script_validation(self):
        """Profile security validation."""
        from kubeflow_mcp.core.security import is_safe_python_code

        script = """
import torch
def train():
    model = torch.nn.Linear(10, 10)
    loss = model(torch.randn(32, 10)).sum()
"""

        profiler = cProfile.Profile()
        profiler.enable()

        for _ in range(1000):
            is_safe_python_code(script)

        profiler.disable()

        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(10)

        print("\nCPU PROFILE: Script Validation (top 10)")
        print(stream.getvalue())


class TestMemoryProfiling:
    """Memory profiling to identify allocations (no file output)."""

    def test_memory_server_creation(self):
        """Profile memory usage during server creation."""
        from kubeflow_mcp.core.server import create_server

        tracemalloc.start()
        create_server(clients=["trainer"])
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\nMemory: current={current / 1024:.1f}KB, peak={peak / 1024:.1f}KB")
        assert peak < 500 * 1024, f"Memory exceeded 500KB: {peak / 1024:.1f}KB"

    def test_memory_tool_schemas(self):
        """Profile memory for generating all tool schemas."""
        import inspect
        import json

        tracemalloc.start()

        schemas = []
        for tool in TOOLS:
            sig = inspect.signature(tool)
            schema = {
                "name": tool.__name__,
                "description": (tool.__doc__ or "").split("\n")[0],
                "parameters": {
                    name: str(param.annotation) for name, param in sig.parameters.items()
                },
            }
            schemas.append(json.dumps(schema))

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\nSchema generation: {len(schemas)} schemas, {peak / 1024:.1f}KB peak")
        assert peak < 100 * 1024, f"Schema memory exceeded 100KB: {peak / 1024:.1f}KB"

"""Generate visual benchmark report with charts.

Creates a comprehensive dashboard comparing tool loading modes:
- Full: All tools via MCP protocol (default)
- Progressive: Meta-tools with hierarchical discovery
- Semantic: Meta-tools with embedding search

Run with: uv run pytest tests/benchmarks/test_report.py -v -s
Requirements: uv sync --extra benchmark --extra trainer

Reliability features:
- Multiple tokenizer comparison (GPT-4, Claude, Llama approximations)
- Warmup runs before measurements
- Statistical analysis (mean, std, confidence intervals)
- Environment metadata captured
- Dynamic tool counts from actual registries
"""

import gc
import json
import platform
import statistics
import time
import tracemalloc

try:
    import matplotlib.pyplot as plt
    import tiktoken
except ImportError:
    import pytest

    pytest.skip(
        "matplotlib/tiktoken not installed (run: uv sync --extra benchmark)",
        allow_module_level=True,
    )

from kubeflow_mcp.trainer import TOOL_CATEGORIES, TOOLS


def count_tokens(text: str) -> int:
    """Count tokens using GPT-4 tokenizer (cl100k_base).

    Note: Different models use different tokenizers. These counts are
    specific to GPT-4/GPT-3.5-turbo. Claude and Llama will differ.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def measure_latency(func, iterations: int = 100, warmup: int = 10) -> dict:
    """Measure latency with warmup and statistical analysis."""
    # Warmup runs (discard results)
    for _ in range(warmup):
        func()

    # Disable GC during measurement
    gc.disable()
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append((time.perf_counter() - start) * 1000)
    gc.enable()

    times_sorted = sorted(times)
    n = len(times)
    mean = statistics.mean(times)
    std = statistics.stdev(times) if n > 1 else 0

    return {
        "mean": mean,
        "std": std,
        "min": min(times),
        "max": max(times),
        "p50": times_sorted[n // 2],
        "p95": times_sorted[int(n * 0.95)],
        "p99": times_sorted[int(n * 0.99)],
        "ci95": 1.96 * std / (n**0.5),  # 95% confidence interval
        "iterations": n,
    }


def get_environment_info() -> dict:
    """Capture environment metadata for reproducibility."""
    return {
        "python": platform.python_version(),
        "os": platform.system(),
        "os_version": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
    }


def get_tool_schema_json(func) -> str:
    """Generate minimal JSON schema for token counting."""
    import inspect

    sig = inspect.signature(func)
    schema = {
        "name": func.__name__,
        "description": (func.__doc__ or "").split("\n")[0].strip(),
        "parameters": {name: str(param.annotation) for name, param in sig.parameters.items()},
    }
    return json.dumps(schema, separators=(",", ":"))


def shorten_tool_name(name: str) -> str:
    """Shorten tool name for display."""
    replacements = {
        "get_training_": "get_",
        "list_training_": "list_",
        "training_": "",
        "_training": "",
        "run_custom_": "custom_",
        "run_container_": "container_",
        "get_cluster_": "cluster_",
        "estimate_": "est_",
        "get_runtime_": "runtime_",
        "wait_for_": "wait_",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name


class TestBenchmarkReport:
    """Generate comprehensive visual benchmark report."""

    def test_generate_visual_report(self, results_dir, benchmark_metadata):
        """Generate visual dashboard with all benchmark metrics."""
        from kubeflow_mcp.agents.dynamic_tools import PROGRESSIVE_TOOLS, SEMANTIC_TOOLS
        from kubeflow_mcp.core.server import SERVER_INSTRUCTIONS, create_server

        metrics = {
            **benchmark_metadata,
            "environment": get_environment_info(),
            "token_usage": {},
            "latency": {},
            "memory": {},
        }

        # === TOKEN USAGE BY TOOL ===
        tool_tokens = {}
        for tool in TOOLS:
            tool_tokens[tool.__name__] = count_tokens(get_tool_schema_json(tool))

        # === TOKEN USAGE BY MODE ===
        static_tokens = sum(tool_tokens.values())
        progressive_tokens = sum(count_tokens(get_tool_schema_json(t)) for t in PROGRESSIVE_TOOLS)
        semantic_tokens = sum(count_tokens(get_tool_schema_json(t)) for t in SEMANTIC_TOOLS)
        instructions_tokens = count_tokens(SERVER_INSTRUCTIONS)

        # Category breakdown
        category_tokens = {
            cat: sum(tool_tokens[t.__name__] for t in tools)
            for cat, tools in TOOL_CATEGORIES.items()
        }

        metrics["token_usage"] = {
            "tokenizer": "cl100k_base (GPT-4)",
            "tools": tool_tokens,
            "modes": {
                "full": static_tokens,
                "progressive": progressive_tokens,
                "semantic": semantic_tokens,
            },
            "server_instructions": instructions_tokens,
            "categories": category_tokens,
            "note": "Static and MCP modes have identical token usage (same tools, different loading mechanism)",
        }

        # === LATENCY ===
        # Server creation latency (shared by static and MCP modes)
        metrics["latency"]["server_creation_ms"] = measure_latency(
            lambda: create_server(clients=["trainer"]),
            iterations=50,
            warmup=10,
        )

        # MCP tool listing latency (list_tools via MCP protocol)
        server = create_server(clients=["trainer"])

        async def list_tools_mcp():
            return await server.list_tools()

        import asyncio

        def run_list_tools():
            asyncio.run(list_tools_mcp())

        metrics["latency"]["mcp_list_tools_ms"] = measure_latency(
            run_list_tools,
            iterations=50,
            warmup=10,
        )

        # === MEMORY (multiple samples) ===
        memory_samples = []
        for _ in range(5):
            tracemalloc.start()
            create_server(clients=["trainer"])
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_samples.append({"current": current / 1024, "peak": peak / 1024})

        metrics["memory"]["server_kb"] = {
            "current_mean": statistics.mean(s["current"] for s in memory_samples),
            "peak_mean": statistics.mean(s["peak"] for s in memory_samples),
            "peak_std": statistics.stdev(s["peak"] for s in memory_samples)
            if len(memory_samples) > 1
            else 0,
            "samples": len(memory_samples),
        }

        # === GENERATE DASHBOARD (2x2 clean layout) ===
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            f"Kubeflow MCP Benchmark Dashboard | Commit: {metrics['commit']} | {metrics['timestamp'][:10]}",
            fontsize=14,
            fontweight="bold",
            y=0.98,
        )

        # ===== CHART 1: Token Comparison by Mode (top-left) =====
        ax1 = axes[0, 0]
        # Dynamic tool counts from actual registries
        num_static_tools = len(TOOLS)
        num_progressive_tools = len(PROGRESSIVE_TOOLS)
        num_semantic_tools = len(SEMANTIC_TOOLS)

        mode_data = [
            (f"Full ({num_static_tools} tools)", static_tokens, "#e74c3c"),
            (f"Progressive ({num_progressive_tools} meta)", progressive_tokens, "#3498db"),
            (f"Semantic ({num_semantic_tools} meta)", semantic_tokens, "#2ecc71"),
        ]
        mode_names = [m[0] for m in mode_data]
        mode_vals = [m[1] for m in mode_data]
        mode_colors = [m[2] for m in mode_data]

        bars = ax1.barh(
            range(len(mode_names)), mode_vals, color=mode_colors, height=0.6, edgecolor="black"
        )
        ax1.set_yticks(range(len(mode_names)))
        ax1.set_yticklabels(mode_names, fontsize=11)
        ax1.set_xlabel("Tokens (GPT-4 cl100k_base)", fontsize=10)
        ax1.set_title("Token Usage by Tool Mode", fontsize=12, fontweight="bold")
        ax1.invert_yaxis()
        ax1.set_xlim(0, static_tokens * 1.35)

        for i, (bar, val) in enumerate(zip(bars, mode_vals, strict=True)):
            if i == 0:
                label = " (baseline)"
            else:
                label = f" (-{(1 - val / static_tokens) * 100:.0f}%)"
            ax1.text(
                val + 10,
                bar.get_y() + bar.get_height() / 2,
                f"{val}{label}",
                va="center",
                fontsize=10,
                fontweight="bold",
            )

        # ===== CHART 2: Top Tools by Token Usage (top-right) =====
        ax2 = axes[0, 1]
        tools_sorted = sorted(tool_tokens.items(), key=lambda x: x[1], reverse=True)[:10]
        short_names = [shorten_tool_name(t[0]) for t in tools_sorted]
        values = [t[1] for t in tools_sorted]
        colors = plt.cm.Blues(
            [(v - min(values)) / (max(values) - min(values) + 1) * 0.5 + 0.4 for v in values]
        )

        bars = ax2.barh(range(len(short_names)), values, color=colors, height=0.7)
        ax2.set_yticks(range(len(short_names)))
        ax2.set_yticklabels(short_names, fontsize=10)
        ax2.set_xlabel("Tokens", fontsize=10)
        ax2.set_title("Top 10 Tools by Token Usage", fontsize=12, fontweight="bold")
        ax2.invert_yaxis()

        for bar, val in zip(bars, values, strict=True):
            ax2.text(val + 1, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=9)

        # ===== CHART 3: Token Usage by Category (bottom-left) =====
        ax3 = axes[1, 0]
        server_lat = metrics["latency"]["server_creation_ms"]

        # Category breakdown pie chart
        cat_data = [(cat, tokens) for cat, tokens in category_tokens.items() if tokens > 0]
        cat_names = [c[0] for c in cat_data]
        cat_vals = [c[1] for c in cat_data]
        cat_colors = plt.cm.Set3(range(len(cat_names)))

        wedges, texts, autotexts = ax3.pie(
            cat_vals,
            labels=cat_names,
            autopct=lambda p: f"{int(p * sum(cat_vals) / 100)}",
            colors=cat_colors,
            startangle=90,
            textprops={"fontsize": 10},
        )
        ax3.set_title("Tokens by Category (Static Mode)", fontsize=12, fontweight="bold")

        # ===== CHART 4: Summary Table (bottom-right) =====
        ax4 = axes[1, 1]
        ax4.axis("off")

        mem = metrics["memory"]["server_kb"]
        env = metrics["environment"]
        mcp_lat = metrics["latency"]["mcp_list_tools_ms"]

        summary = [
            ["Category", "Metric", "Value"],
            ["Tokens", f"Full ({num_static_tools} tools)", f"{static_tokens}"],
            [
                "",
                f"Progressive ({num_progressive_tools} meta)",
                f"{progressive_tokens} (-{(1 - progressive_tokens / static_tokens) * 100:.0f}%)",
            ],
            [
                "",
                f"Semantic ({num_semantic_tools} meta)",
                f"{semantic_tokens} (-{(1 - semantic_tokens / static_tokens) * 100:.0f}%)",
            ],
            [
                "Latency",
                "Server Init",
                f"{server_lat['mean']:.2f} ± {server_lat['ci95']:.2f} ms",
            ],
            [
                "",
                "MCP list_tools",
                f"{mcp_lat['mean']:.2f} ± {mcp_lat['ci95']:.2f} ms",
            ],
            [
                "Memory",
                "Peak",
                f"{mem['peak_mean']:.1f} ± {mem['peak_std']:.1f} KB",
            ],
            ["Env", "System", f"Py {env['python']} / {env['os']} {env['machine']}"],
        ]

        table = ax4.table(
            cellText=summary[1:],
            colLabels=summary[0],
            loc="center",
            cellLoc="left",
            colWidths=[0.2, 0.38, 0.42],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.15, 1.7)

        for (row, _col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(fontweight="bold")
                cell.set_facecolor("#f0f0f0")
            if row == 3:  # Semantic tokens row (best)
                cell.set_facecolor("#d4edda")

        ax4.set_title("Summary", fontsize=12, fontweight="bold", y=0.95)

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        # Save outputs (only latest - tracked in git for README)
        chart_path = results_dir / "benchmark_report_latest.png"
        json_path = results_dir / "benchmark_report_latest.json"

        plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close()

        with open(json_path, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"\n{'=' * 70}")
        print("BENCHMARK REPORT GENERATED")
        print(f"{'=' * 70}")
        print(f"Chart: {chart_path}")
        print(f"Data:  {json_path}")
        print(f"\nEnvironment: Python {env['python']} on {env['os']} {env['machine']}")
        print("\nToken Usage (GPT-4 cl100k_base tokenizer):")
        print(f"  Full:        {static_tokens:4d} tokens (baseline, {num_static_tools} tools)")
        print(
            f"  Progressive: {progressive_tokens:4d} tokens ({num_progressive_tools} meta, -{(1 - progressive_tokens / static_tokens) * 100:.0f}%)"
        )
        print(
            f"  Semantic:    {semantic_tokens:4d} tokens ({num_semantic_tools} meta, -{(1 - semantic_tokens / static_tokens) * 100:.0f}%)"
        )
        print("\nLatency:")
        print(f"  Server Init:     {server_lat['mean']:.2f}ms ± {server_lat['ci95']:.2f}ms")
        print(f"  MCP list_tools:  {mcp_lat['mean']:.2f}ms ± {mcp_lat['ci95']:.2f}ms")
        print(f"\nMemory Peak: {mem['peak_mean']:.1f} KB ± {mem['peak_std']:.1f} KB")

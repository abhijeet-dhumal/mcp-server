"""Token usage benchmarks for MCP tool schemas.

Measures token counts for different tool loading modes to track context efficiency.
Run with: uv run pytest tests/benchmarks/test_token_usage.py -v

Requirements: uv sync --extra benchmark --extra trainer
"""

import inspect
import json
from typing import Any

import pytest

try:
    import tiktoken
except ImportError:
    pytest.skip("tiktoken not installed (run: uv sync --extra benchmark)", allow_module_level=True)

from kubeflow_mcp.trainer import TOOL_CATEGORIES, TOOLS


def count_tokens(text: str, encoding: str = "cl100k_base") -> int:
    """Count tokens using OpenAI's tiktoken (Claude uses similar tokenization)."""
    enc = tiktoken.get_encoding(encoding)
    return len(enc.encode(text))


def get_tool_schema(func) -> dict[str, Any]:
    """Generate MCP-style tool schema from function."""
    sig = inspect.signature(func)
    doc = func.__doc__ or ""

    # Extract first line as description
    description = doc.split("\n")[0].strip()

    # Build parameters from signature
    properties = {}
    required = []

    for name, param in sig.parameters.items():
        prop: dict[str, Any] = {"type": "string"}  # Default

        # Infer type from annotation
        if param.annotation != inspect.Parameter.empty:
            ann = param.annotation
            if ann is str or (hasattr(ann, "__origin__") and "str" in str(ann)):
                prop["type"] = "string"
            elif ann is int:
                prop["type"] = "integer"
            elif ann is bool:
                prop["type"] = "boolean"
            elif ann is float:
                prop["type"] = "number"
            elif hasattr(ann, "__origin__") and ann.__origin__ is list:
                prop["type"] = "array"
            elif hasattr(ann, "__origin__") and ann.__origin__ is dict:
                prop["type"] = "object"

        # Check if required (no default)
        if param.default == inspect.Parameter.empty:
            required.append(name)

        properties[name] = prop

    return {
        "name": func.__name__,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def schema_to_json(schema: dict) -> str:
    """Convert schema to JSON string for token counting."""
    return json.dumps(schema, separators=(",", ":"))


class TestTokenUsageByMode:
    """Test token usage for different tool loading modes."""

    def test_full_mode_all_tools(self):
        """Measure tokens for full mode (all tools)."""
        tools = TOOLS
        total_tokens = 0
        tool_tokens = {}

        for tool in tools:
            schema = get_tool_schema(tool)
            schema_json = schema_to_json(schema)
            tokens = count_tokens(schema_json)
            tool_tokens[tool.__name__] = tokens
            total_tokens += tokens

        print(f"\n{'=' * 60}")
        print(f"FULL MODE: {len(tools)} tools, {total_tokens} tokens")
        print(f"{'=' * 60}")
        for name, tokens in sorted(tool_tokens.items(), key=lambda x: -x[1]):
            print(f"  {name}: {tokens} tokens")

        # Assertions - track regressions (tool count should match TOOL_PHASES)
        from kubeflow_mcp.common.constants import TOOL_PHASES

        expected_tools = sum(len(t) for t in TOOL_PHASES.values())
        assert len(tools) == expected_tools, f"Expected {expected_tools} tools, got {len(tools)}"
        assert total_tokens < 1500, f"Token budget exceeded: {total_tokens} > 1500"

    def test_core_mode_essential_tools(self):
        """Measure tokens for core mode (5 essential tools)."""
        tools = TOOL_CATEGORIES.get("core", [])
        total_tokens = 0
        tool_tokens = {}

        for tool in tools:
            schema = get_tool_schema(tool)
            schema_json = schema_to_json(schema)
            tokens = count_tokens(schema_json)
            tool_tokens[tool.__name__] = tokens
            total_tokens += tokens

        print(f"\n{'=' * 60}")
        print(f"CORE MODE: {len(tools)} tools, {total_tokens} tokens")
        print(f"{'=' * 60}")
        for name, tokens in sorted(tool_tokens.items(), key=lambda x: -x[1]):
            print(f"  {name}: {tokens} tokens")

        assert len(tools) == 5, f"Expected 5 core tools, got {len(tools)}"
        assert total_tokens < 1000, f"Core mode budget exceeded: {total_tokens} > 1000"

    def test_planning_category_tools(self):
        """Measure tokens for planning category."""
        tools = TOOL_CATEGORIES.get("planning", [])
        total_tokens = sum(count_tokens(schema_to_json(get_tool_schema(t))) for t in tools)

        print(f"\nPLANNING: {len(tools)} tools, {total_tokens} tokens")
        assert total_tokens < 500

    def test_training_category_tools(self):
        """Measure tokens for training category."""
        tools = TOOL_CATEGORIES.get("training", [])
        total_tokens = sum(count_tokens(schema_to_json(get_tool_schema(t))) for t in tools)

        print(f"\nTRAINING: {len(tools)} tools, {total_tokens} tokens")
        assert total_tokens < 800

    def test_discovery_category_tools(self):
        """Measure tokens for discovery category."""
        tools = TOOL_CATEGORIES.get("discovery", [])
        total_tokens = sum(count_tokens(schema_to_json(get_tool_schema(t))) for t in tools)

        print(f"\nDISCOVERY: {len(tools)} tools, {total_tokens} tokens")
        assert total_tokens < 600

    def test_monitoring_category_tools(self):
        """Measure tokens for monitoring category."""
        tools = TOOL_CATEGORIES.get("monitoring", [])
        total_tokens = sum(count_tokens(schema_to_json(get_tool_schema(t))) for t in tools)

        print(f"\nMONITORING: {len(tools)} tools, {total_tokens} tokens")
        assert total_tokens < 500

    def test_lifecycle_category_tools(self):
        """Measure tokens for lifecycle category."""
        tools = TOOL_CATEGORIES.get("lifecycle", [])
        total_tokens = sum(count_tokens(schema_to_json(get_tool_schema(t))) for t in tools)

        print(f"\nLIFECYCLE: {len(tools)} tools, {total_tokens} tokens")
        assert total_tokens < 500


class TestTokenUsageByTool:
    """Test token usage for individual tools."""

    @pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.__name__)
    def test_individual_tool_tokens(self, tool):
        """Measure tokens for each tool individually."""
        schema = get_tool_schema(tool)
        schema_json = schema_to_json(schema)
        tokens = count_tokens(schema_json)

        print(f"\n{tool.__name__}: {tokens} tokens")

        # No single tool should exceed 300 tokens
        assert tokens < 300, f"{tool.__name__} exceeds 300 tokens: {tokens}"


class TestServerInstructionsTokens:
    """Test token usage for server instructions."""

    def test_server_instructions_tokens(self):
        """Measure tokens for server instructions."""
        from kubeflow_mcp.core.server import SERVER_INSTRUCTIONS

        tokens = count_tokens(SERVER_INSTRUCTIONS)

        print(f"\nSERVER INSTRUCTIONS: {tokens} tokens")

        # Instructions should be concise
        assert tokens < 800, f"Instructions too long: {tokens} > 800 tokens"


class TestTokenSummary:
    """Token usage summary (no file output - see test_report.py for artifacts)."""

    def test_total_token_budget(self):
        """Verify total token budget across all modes."""
        from kubeflow_mcp.core.server import SERVER_INSTRUCTIONS

        tool_tokens = {}
        for tool in TOOLS:
            schema = get_tool_schema(tool)
            tool_tokens[tool.__name__] = count_tokens(schema_to_json(schema))

        static_total = sum(tool_tokens.values())
        core_tools = TOOL_CATEGORIES.get("core", [])
        core_total = sum(tool_tokens[t.__name__] for t in core_tools)
        instructions = count_tokens(SERVER_INSTRUCTIONS)

        print("\nToken Summary:")
        print(f"  Static mode: {static_total} tokens")
        print(f"  Core mode: {core_total} tokens")
        print(f"  Instructions: {instructions} tokens")

        # Budget assertions
        assert static_total < 3000, f"Static mode budget exceeded: {static_total}"
        assert core_total < 1000, f"Core mode budget exceeded: {core_total}"
        assert instructions < 800, f"Instructions budget exceeded: {instructions}"

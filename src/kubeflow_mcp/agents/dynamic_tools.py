"""Dynamic toolsets for token-efficient tool discovery.

Implements two approaches from https://www.speakeasy.com/blog/100x-token-reduction-dynamic-toolsets:
1. Progressive Search - Hierarchical discovery with prefix-based lookup
2. Semantic Search - Embeddings-based natural language discovery

Usage:
    # Progressive mode (~3K initial tokens)
    agent = OllamaAgent(model="qwen2.5:7b", tool_mode="progressive")

    # Semantic mode (~2K initial tokens, requires sentence-transformers)
    agent = OllamaAgent(model="qwen2.5:7b", tool_mode="semantic")

    # Static mode (all tools, ~5K tokens) - default
    agent = OllamaAgent(model="qwen2.5:7b", tool_mode="static")
"""

from collections.abc import Callable
from typing import Any

from kubeflow_mcp.trainer import TOOLS

# Build tool registry with hierarchy
TOOL_REGISTRY: dict[str, dict[str, Any]] = {}
TOOL_HIERARCHY: dict[str, list[str]] = {
    "planning": [],
    "training": [],
    "discovery": [],
    "monitoring": [],
    "lifecycle": [],
}

# Categorize tools
TOOL_CATEGORIES_MAP = {
    "get_cluster_resources": "planning",
    "estimate_resources": "planning",
    "fine_tune": "training",
    "run_custom_training": "training",
    "run_container_training": "training",
    "list_training_jobs": "discovery",
    "get_training_job": "discovery",
    "list_runtimes": "discovery",
    "get_runtime": "discovery",
    "get_runtime_packages": "discovery",
    "get_training_logs": "monitoring",
    "get_training_events": "monitoring",
    "wait_for_training": "monitoring",
    "delete_training_job": "lifecycle",
    "suspend_training_job": "lifecycle",
    "resume_training_job": "lifecycle",
}

# Build registry
for tool_func in TOOLS:
    name = tool_func.__name__
    doc = tool_func.__doc__ or ""
    category = TOOL_CATEGORIES_MAP.get(name, "other")

    TOOL_REGISTRY[name] = {
        "name": name,
        "category": category,
        "description": doc.split("\n")[0] if doc else name,
        "full_doc": doc,
        "func": tool_func,
    }
    TOOL_HIERARCHY[category].append(name)


# =============================================================================
# Progressive Search Implementation
# =============================================================================


def list_tools(prefix: str = "") -> dict[str, Any]:
    """List available tools by category or prefix.

    Use this to discover what tools are available. Start with no prefix to see
    categories, then drill down with specific prefixes.

    Args:
        prefix: Filter prefix. Examples:
            - "" → List all categories
            - "planning" → List planning tools
            - "training" → List training tools
            - "discovery" → List discovery tools

    Returns:
        {categories: [...], tools: [...]} based on prefix

    Example workflow:
        1. list_tools() → See categories: planning, training, discovery, monitoring, lifecycle
        2. list_tools("training") → See: fine_tune, run_custom_training, run_container_training
        3. describe_tools(["fine_tune"]) → Get full schema for fine_tune
        4. execute_tool("fine_tune", {model: "...", dataset: "..."})
    """
    if not prefix:
        # Return categories overview
        return {
            "categories": list(TOOL_HIERARCHY.keys()),
            "category_tools": {cat: len(tools) for cat, tools in TOOL_HIERARCHY.items()},
            "hint": "Use list_tools('category_name') to see tools in a category",
        }

    # Check if prefix is a category
    if prefix in TOOL_HIERARCHY:
        tools = TOOL_HIERARCHY[prefix]
        return {
            "category": prefix,
            "tools": [
                {"name": t, "description": TOOL_REGISTRY[t]["description"]} for t in tools
            ],
            "hint": "Use describe_tools(['tool_name']) to get full schema",
        }

    # Search by tool name prefix
    matching = [
        {"name": name, "description": info["description"]}
        for name, info in TOOL_REGISTRY.items()
        if name.startswith(prefix) or prefix in name
    ]

    return {
        "prefix": prefix,
        "matching_tools": matching,
        "hint": "Use describe_tools(['tool_name']) to get full schema",
    }


def describe_tools(tool_names: list[str]) -> dict[str, Any]:
    """Get detailed schema for specific tools.

    Call this after list_tools() to get full parameter information before executing.

    Args:
        tool_names: List of tool names to describe (max 5 at a time)

    Returns:
        {tools: [{name, description, parameters, returns}]}
    """
    if len(tool_names) > 5:
        return {"error": "Max 5 tools at a time to conserve tokens"}

    results: list[dict[str, Any]] = []
    for name in tool_names:
        if name not in TOOL_REGISTRY:
            results.append({"name": name, "error": "Tool not found"})
            continue

        tool = TOOL_REGISTRY[name]
        func = tool["func"]

        # Extract parameter info from function signature
        import inspect

        sig = inspect.signature(func)
        params: dict[str, Any] = {}
        for param_name, param in sig.parameters.items():
            param_info: dict[str, Any] = {"type": "any"}
            if param.annotation != inspect.Parameter.empty:
                param_info["type"] = str(param.annotation)
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            params[param_name] = param_info

        results.append(
            {
                "name": name,
                "category": tool["category"],
                "description": tool["full_doc"],
                "parameters": params,
            }
        )

    return {"tools": results}


def execute_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a discovered tool.

    Call this after using list_tools() and describe_tools() to run the actual tool.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as key-value pairs

    Returns:
        Tool execution result
    """
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found", "available": list(TOOL_REGISTRY.keys())}

    func = TOOL_REGISTRY[tool_name]["func"]
    args = arguments or {}

    try:
        result = func(**args)
        return result if isinstance(result, dict) else {"result": result}
    except Exception as e:
        return {"error": str(e), "tool": tool_name, "arguments": args}


# Progressive search meta-tools (3 tools instead of 16)
PROGRESSIVE_TOOLS = [list_tools, describe_tools, execute_tool]


# =============================================================================
# Semantic Search Implementation
# =============================================================================

# Pre-computed tool descriptions for embedding
TOOL_DESCRIPTIONS_FOR_EMBEDDING = {
    name: f"{info['description']}. Category: {info['category']}. {info['full_doc'][:200]}"
    for name, info in TOOL_REGISTRY.items()
}

_embeddings_cache: dict[str, list[float]] | None = None
_model_cache = None


def _get_embeddings():
    """Lazy-load embeddings for all tools."""
    global _embeddings_cache, _model_cache

    if _embeddings_cache is not None:
        return _embeddings_cache, _model_cache

    try:
        from sentence_transformers import SentenceTransformer

        # Use a small, fast model
        _model_cache = SentenceTransformer("all-MiniLM-L6-v2")

        # Create embeddings for all tools
        descriptions = list(TOOL_DESCRIPTIONS_FOR_EMBEDDING.values())
        embeddings = _model_cache.encode(descriptions)

        _embeddings_cache = {
            name: emb.tolist()
            for name, emb in zip(TOOL_DESCRIPTIONS_FOR_EMBEDDING.keys(), embeddings, strict=True)
        }

        return _embeddings_cache, _model_cache

    except ImportError:
        return None, None


def find_tools(query: str, top_k: int = 5) -> dict[str, Any]:
    """Find relevant tools using semantic search.

    Describe what you want to accomplish in natural language, and this will
    return the most relevant tools.

    Args:
        query: Natural language description of what you want to do. Examples:
            - "check GPU availability in the cluster"
            - "fine-tune a language model"
            - "view logs from a training job"
            - "delete a failed job"
        top_k: Number of results to return (default 5)

    Returns:
        {tools: [{name, description, score}], hint: "Use execute_tool(name, args)"}
    """
    embeddings, model = _get_embeddings()

    if embeddings is None:
        # Fallback to keyword search
        return _keyword_search(query, top_k)

    import numpy as np

    # Embed the query
    query_embedding = model.encode([query])[0]

    # Compute cosine similarities
    scores = {}
    for name, tool_emb in embeddings.items():
        similarity = np.dot(query_embedding, tool_emb) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(tool_emb)
        )
        scores[name] = float(similarity)

    # Sort by score
    sorted_tools = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    return {
        "query": query,
        "tools": [
            {
                "name": name,
                "description": TOOL_REGISTRY[name]["description"],
                "category": TOOL_REGISTRY[name]["category"],
                "relevance": f"{score:.2f}",
            }
            for name, score in sorted_tools
        ],
        "hint": "Use execute_tool(tool_name, {args}) to run a tool",
    }


def _keyword_search(query: str, top_k: int = 5) -> dict[str, Any]:
    """Fallback keyword search when embeddings unavailable."""
    query_lower = query.lower()
    keywords = query_lower.split()

    scores = {}
    for name, info in TOOL_REGISTRY.items():
        text = f"{name} {info['description']} {info['category']}".lower()
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[name] = score

    sorted_tools = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    return {
        "query": query,
        "mode": "keyword_fallback",
        "tools": [
            {
                "name": name,
                "description": TOOL_REGISTRY[name]["description"],
                "category": TOOL_REGISTRY[name]["category"],
            }
            for name, _ in sorted_tools
        ],
        "hint": "Use execute_tool(tool_name, {args}) to run a tool",
    }


# Semantic search meta-tools (2 tools instead of 16)
SEMANTIC_TOOLS = [find_tools, execute_tool]


# =============================================================================
# Factory Functions
# =============================================================================


def get_dynamic_tools(mode: str = "progressive") -> list[Callable[..., Any]]:
    """Get meta-tools for dynamic discovery.

    Args:
        mode: "progressive" or "semantic"

    Returns:
        List of meta-tool functions
    """
    if mode == "semantic":
        return SEMANTIC_TOOLS  # type: ignore[return-value]
    return PROGRESSIVE_TOOLS  # type: ignore[return-value]


def get_dynamic_system_prompt(mode: str = "progressive") -> str:
    """Get system prompt for dynamic tool mode."""
    if mode == "semantic":
        return """Kubeflow training assistant. Run full workflow without pausing.

WORKFLOW (run ALL in one turn, only pause for final confirmation):
1. find_tools → get_cluster_resources → execute
2. find_tools → estimate_resources → execute
3. find_tools → list_runtimes → execute
4. find_tools → fine_tune(confirmed=False) → execute → SHOW PREVIEW
5. WAIT for user confirmation
6. fine_tune(confirmed=True)

CRITICAL: Do NOT pause between steps 1-4. Run them all, then show preview and wait.
Use hf:// prefix for model/dataset URIs.
"""

    return """Kubeflow training assistant. Run full workflow without pausing.

WORKFLOW (run ALL in one turn, only pause for final confirmation):
1. list_tools("planning") → execute get_cluster_resources, estimate_resources
2. list_tools("discovery") → execute list_runtimes
3. list_tools("training") → execute fine_tune(confirmed=False) → SHOW PREVIEW
4. WAIT for user confirmation
5. fine_tune(confirmed=True)

CRITICAL: Do NOT pause between steps 1-3. Run them all, then show preview and wait.
Use hf:// prefix for model/dataset URIs.
"""

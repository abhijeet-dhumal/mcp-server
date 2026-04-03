# Development Guide

This guide helps new contributors get started with kubeflow-mcp development.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Access to a Kubernetes cluster (optional, for integration testing)
- [Ollama](https://ollama.ai/) (optional, for agent testing)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/kubeflow/mcp-server.git
cd mcp-server

# Install all dependencies (includes dev tools)
make install

# Run linting and tests
make pre-commit

# Start the MCP server
make serve
```

## Project Structure

```
mcp-server/
├── src/kubeflow_mcp/       # Main source code
│   ├── core/               # Server infrastructure
│   ├── trainer/            # Kubeflow Training tools
│   ├── agents/             # Local agent implementations
│   └── cli.py              # CLI entry point
├── tests/
│   ├── unit/               # Unit tests (no cluster needed)
│   └── benchmarks/         # Performance benchmarks
├── examples/               # Example scripts
├── assets/                 # Images for documentation
└── docs/                   # Additional documentation
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/add-new-tool
```

### 2. Make Your Changes

Edit files in `src/kubeflow_mcp/`. See [ARCHITECTURE.md](ARCHITECTURE.md) for module overview.

### 3. Run Quality Checks

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make typecheck

# Run all tests
make test
```

### 4. Test Manually

```bash
# Start server
make serve

# In another terminal, test with Ollama agent
make agent
```

### 5. Submit PR

```bash
git add .
git commit -s -m "feat: add new tool for X"
git push origin feature/add-new-tool
```

## Adding a New Tool

### Step 1: Create the Tool Function

```python
# src/kubeflow_mcp/trainer/api/your_module.py

from kubeflow_mcp.core.types import ToolResponse, ToolError

def your_new_tool(
    param1: str,
    param2: int = 10,
) -> dict:
    """Short description (shown in tool list).
    
    Detailed description for LLMs explaining:
    - When to use this tool
    - What parameters mean
    - What the response contains
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
    
    Returns:
        dict with keys: result, details
    """
    try:
        # Your implementation here
        result = do_something(param1, param2)
        return ToolResponse(
            success=True,
            result=result,
        )
    except SomeError as e:
        return ToolError(
            error=str(e),
            error_code="YOUR_ERROR_CODE",
        )
```

### Step 2: Register the Tool

```python
# src/kubeflow_mcp/trainer/__init__.py

from .api.your_module import your_new_tool

TOOLS: list[Callable] = [
    # ... existing tools ...
    your_new_tool,
]

TOOL_CATEGORIES: dict[str, list[str]] = {
    # Add to appropriate category
    "discovery": [
        # ... existing tools ...
        "your_new_tool",
    ],
}
```

### Step 3: Add Annotations

```python
# src/kubeflow_mcp/core/server.py

TOOL_ANNOTATIONS: dict[str, dict] = {
    # ... existing annotations ...
    "your_new_tool": {
        "title": "Your New Tool",
        "readOnlyHint": True,      # True if no side effects
        "destructiveHint": False,   # True if deletes data
        "idempotentHint": True,     # True if safe to retry
        "openWorldHint": True,      # True if calls external services
    },
}
```

### Step 4: Write Tests

```python
# tests/unit/trainer/test_your_module.py

import pytest
from kubeflow_mcp.trainer.api.your_module import your_new_tool

class TestYourNewTool:
    def test_basic_usage(self):
        result = your_new_tool("value", param2=5)
        assert result["success"] is True
    
    def test_error_handling(self):
        result = your_new_tool("invalid")
        assert result["success"] is False
        assert "error" in result
```

### Step 5: Update Documentation

Add the tool to `README.md` in the "Available Tools" section.

## Testing Without a Cluster

Most tests run without a Kubernetes cluster by mocking the SDK:

```python
from unittest.mock import patch, MagicMock

@patch("kubeflow_mcp.trainer.client.get_trainer_client")
def test_list_jobs(mock_client):
    mock_client.return_value.list_jobs.return_value = [
        MagicMock(name="job-1"),
    ]
    result = list_training_jobs()
    assert len(result["jobs"]) == 1
```

## Integration Testing

If you have cluster access:

```bash
# Set kubeconfig
export KUBECONFIG=~/.kube/config

# Run integration tests
pytest tests/integration/ -v
```

## Debugging Tips

### Enable Debug Logging

```bash
kubeflow-mcp serve --log-level debug
```

### Test a Single Tool

```python
# In Python REPL
from kubeflow_mcp.trainer.api.planning import get_cluster_resources
print(get_cluster_resources())
```

### Inspect MCP Messages

Use [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector):

```bash
npx @anthropic/mcp-inspector kubeflow-mcp serve
```

## Benchmarking

```bash
# Run benchmarks (generates report)
make benchmark

# View results
open tests/benchmarks/benchmark_report_latest.png
```

## Common Issues

### Import Errors

```bash
# Ensure you're using the local development version
pip uninstall kubeflow-mcp
uv sync --extra dev --extra trainer
```

### SDK Version Mismatch

```bash
# Check installed SDK version
python -c "import kubeflow; print(kubeflow.__version__)"

# Should be 0.4.0+
```

### Linting Failures

```bash
# Auto-fix most issues
make format

# Then run lint again
make lint
```

## Getting Help

- Open an issue on GitHub
- Join [Kubeflow Slack](https://kubeflow.slack.com) #wg-training
- Review existing code for patterns

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [Kubeflow Training Docs](https://www.kubeflow.org/docs/components/training/)

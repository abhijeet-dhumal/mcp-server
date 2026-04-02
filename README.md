# Kubeflow MCP Server

AI-powered interface for Kubeflow Training via [Model Context Protocol](https://modelcontextprotocol.io/).

## Installation

```bash
uv sync
```

## Usage

### Cursor / Claude Desktop

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "kubeflow": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-server", "kubeflow-mcp", "serve"]
    }
  }
}
```

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run kubeflow-mcp serve
```

### Local Agent (Ollama)

```bash
uv sync --extra agents
uv run python -m kubeflow_mcp.agents.ollama --model qwen2.5:7b
```

### CLI

```bash
kubeflow-mcp serve --clients trainer --persona ml-engineer
```

## Tools

| Category | Tools |
|----------|-------|
| Planning | `get_cluster_resources`, `estimate_resources` |
| Training | `fine_tune`, `run_custom_training`, `run_container_training` |
| Discovery | `list_training_jobs`, `get_training_job`, `list_runtimes`, `get_runtime`, `get_runtime_packages` |
| Monitoring | `get_training_logs`, `get_training_events`, `wait_for_training` |
| Lifecycle | `delete_training_job`, `suspend_training_job`, `resume_training_job` |

## Skills

Reference with `@skills/trainer/SKILL.md` in Cursor.

## Development

```bash
uv sync --all-extras
uv run pytest
uv run ruff check .
```

## Status

| Component | Status |
|-----------|--------|
| TrainerClient | ✅ 16 tools |
| OptimizerClient | ⬜ Contributors welcome |
| ModelRegistryClient | ⬜ Contributors welcome |

## License

Apache-2.0

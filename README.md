# Kubeflow MCP Server

AI-powered interface for Kubeflow Training via [Model Context Protocol](https://modelcontextprotocol.io/).

## Quick Start

```bash
# Install
uv sync

# Run
uv run kubeflow-mcp serve
```

## Usage

### With Cursor/Claude Desktop

Add to `~/.cursor/mcp.json` (or `claude_desktop_config.json`):

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

### With MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run kubeflow-mcp serve
# Open http://localhost:6274
```

### CLI Options

```bash
kubeflow-mcp serve \
  --clients trainer \
  --persona ml-engineer \
  --log-level INFO
```

## Tools (16)

| Category | Tools |
|----------|-------|
| Planning | `get_cluster_resources`, `estimate_resources` |
| Training | `fine_tune`, `run_custom_training`, `run_container_training` |
| Discovery | `list_training_jobs`, `get_training_job`, `list_runtimes`, `get_runtime`, `get_runtime_packages` |
| Monitoring | `get_training_logs`, `get_training_events`, `wait_for_training` |
| Lifecycle | `delete_training_job`, `suspend_training_job`, `resume_training_job` |

## Skills

Reference in Cursor with `@skills/trainer/SKILL.md`:
- `SKILL.md` - Tool overview and workflows
- `fine-tuning.md` - Fine-tuning guide
- `custom-training.md` - Custom scripts
- `troubleshooting.md` - Error recovery

## Development

```bash
uv sync --all-extras
uv run pytest
uv run ruff check .
```

## Status

| Component | Status |
|-----------|--------|
| TrainerClient (16 tools) | ✅ Complete |
| OptimizerClient | ⬜ Contributors Welcome |
| ModelRegistryClient | ⬜ Contributors Welcome |

## License

Apache-2.0

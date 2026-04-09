# Kubeflow MCP Server

AI-powered interface for Kubeflow Training via [Model Context Protocol](https://modelcontextprotocol.io/).

Proposal: https://github.com/kubeflow/community/tree/master/proposals/936-kubeflow-mcp-server

> ⚠️ **Note:** This project is in early development. We currently accept PRs only after prior discussion on Slack — join `#kubeflow-ml-experience` on the [CNCF Slack](https://www.kubeflow.org/docs/about/community/).

## Overview

This MCP server enables LLM agents (Claude, Cursor, etc.) to interact with Kubeflow Training through natural language. It wraps the [Kubeflow SDK](https://github.com/kubeflow/sdk) with MCP tools for fine-tuning, training job management, and monitoring.

## Status

| Component | Status |
|-----------|--------|
| Core Infrastructure | 🚧 In Progress |
| TrainerClient Tools | 🚧 In Progress |
| OptimizerClient Tools | ⬜ Planned (Contributors Welcome) |
| ModelRegistryClient Tools | ⬜ Planned (Contributors Welcome) |

## Quick Start

```bash
# Install
pip install kubeflow-mcp[trainer]

# Run
kubeflow-mcp serve --clients trainer
```

## Development

```bash
# Clone
git clone https://github.com/kubeflow/mcp-server.git
cd mcp-server

# Setup
uv sync --all-extras

# Test
uv run pytest

# Lint
uv run ruff check .
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache License 2.0 - See [LICENSE](LICENSE)

# Kubeflow MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

AI-powered interface for Kubeflow Training via [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).
Enable your AI assistants to manage distributed training jobs, fine-tune LLMs, and monitor workloads
on Kubernetes — all through natural language.

## Overview

The Kubeflow MCP Server bridges AI assistants (Claude, Cursor, custom agents) with Kubeflow's
training infrastructure. Instead of writing YAML manifests or learning Kubernetes APIs, simply
describe what you want to train and let AI handle the complexity.

### Key Benefits

- **Natural Language Interface**: Describe training jobs in plain English — "fine-tune Llama-3 on my dataset with 4 GPUs"
- **Smart Resource Planning**: AI estimates GPU/memory requirements before job submission
- **Real-time Monitoring**: Stream logs, track progress, and debug failures conversationally
- **Safe by Design**: Preview configurations before submission, built-in validation and guardrails
- **Multi-Client Support**: Works with Claude Desktop, Cursor IDE, MCP Inspector, or custom Ollama agents

## Quick Start

### Install

```bash
# Using uv (recommended)
pip install uv
uv sync

# Or with pip
pip install kubeflow-mcp
```

### Configure Your AI Assistant

<details>
<summary><b>Cursor IDE</b></summary>

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
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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
</details>

<details>
<summary><b>MCP Inspector (Debug)</b></summary>

```bash
npx @modelcontextprotocol/inspector uv run kubeflow-mcp serve
```
</details>

### Try It Out

Once configured, ask your AI assistant:

```
"What training jobs are running in my cluster?"
"Fine-tune google/gemma-2b on squad dataset with 2 GPUs"
"Show me logs for the failed training job"
"How many GPUs do I need to fine-tune Llama-3-8B?"
```

## Local Agent (Ollama)

Run a fully local AI agent powered by Ollama — no cloud APIs required:

```bash
# Install with agent support
uv sync --extra agents

# Pull a model with tool-calling support
ollama pull qwen2.5:7b

# Start the interactive agent
uv run python -m kubeflow_mcp.agents.ollama --model qwen2.5:7b
```

**Recommended models for tool calling:**
- `qwen2.5:7b` — Fast, reliable tool calling (7GB RAM)
- `qwen3:8b` — Thinking + tool calling support (8GB RAM)
- `phi4-mini-reasoning` — Reasoning with tools (8GB RAM)

## Available Tools

| Category | Tools | Description |
|----------|-------|-------------|
| **Planning** | `get_cluster_resources`, `estimate_resources` | Check cluster capacity, estimate job requirements |
| **Training** | `fine_tune`, `run_custom_training`, `run_container_training` | Submit LLM fine-tuning or custom training jobs |
| **Discovery** | `list_training_jobs`, `get_training_job`, `list_runtimes`, `get_runtime` | Browse jobs and available training runtimes |
| **Monitoring** | `get_training_logs`, `get_training_events`, `wait_for_training` | Stream logs, watch events, wait for completion |
| **Lifecycle** | `delete_training_job`, `suspend_training_job`, `resume_training_job` | Manage job lifecycle |

### Example: Fine-tune an LLM

```python
# The AI assistant calls this behind the scenes
fine_tune(
    model="google/gemma-2b",
    dataset="squad",
    num_nodes=2,
    gpu_per_node=1,
    confirmed=True
)
```

### Example: Resource Estimation

Ask: *"How much GPU memory do I need for Llama-3-70B?"*

The server fetches model info from HuggingFace and calculates:
```json
{
  "model": "meta-llama/Llama-3-70B",
  "parameters": "70B",
  "estimated_memory_gb": 140,
  "recommended_gpus": 4,
  "gpu_type": "A100-80GB"
}
```

## CLI Reference

```bash
# Start MCP server (default)
kubeflow-mcp serve

# Specify clients and persona
kubeflow-mcp serve --clients trainer --persona ml-engineer

# Available personas: ml-engineer, admin, viewer
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Assistant                            │
│              (Claude / Cursor / Ollama Agent)               │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kubeflow MCP Server                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Planning   │  │  Training   │  │     Monitoring      │  │
│  │   Tools     │  │   Tools     │  │       Tools         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ Kubeflow SDK
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                        │
│           (Kubeflow Training Operator / TrainJobs)          │
└─────────────────────────────────────────────────────────────┘
```

## Cursor Skills

Enhance AI context with training skills:

```
@skills/trainer/SKILL.md
```

Skills provide domain knowledge about Kubeflow training patterns, helping the AI make better decisions.

## Development

```bash
# Install all dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint and type check
uv run ruff check .
uv run mypy src/

# Format code
uv run ruff format .
```

## Roadmap

| Component | Status | Tools |
|-----------|--------|-------|
| **TrainerClient** | ✅ Available | 16 tools |
| **OptimizerClient** | 🚧 Planned | Hyperparameter tuning |
| **ModelRegistryClient** | 🚧 Planned | Model versioning |
| **SparkClient** | 🚧 Planned | Data processing |

## Community

- **Slack**: Join [#kubeflow-ml-experience](https://www.kubeflow.org/docs/about/community/#kubeflow-slack-channels)
- **Meetings**: [Kubeflow SDK and ML Experience](https://bit.ly/kf-ml-experience) bi-weekly calls
- **GitHub**: Issues and PRs welcome!

## Contributing

We welcome contributions! Areas where help is needed:

- [ ] OptimizerClient integration (Katib)
- [ ] ModelRegistryClient integration
- [ ] Additional training runtimes
- [ ] More agent backends (OpenAI, Anthropic API)

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache-2.0

# Kubeflow MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Kubeflow SDK](https://img.shields.io/badge/Kubeflow_SDK-≥0.4.0-orange.svg)](https://pypi.org/project/kubeflow/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Status](https://img.shields.io/badge/Status-Early_Development-yellow.svg)](#project-status)

AI-powered interface for Kubeflow Training via [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).
Enable your AI assistants to manage distributed training jobs, fine-tune LLMs, and monitor workloads
on Kubernetes — all through natural language.

> **Note**: This project is in early development. APIs may change between versions.

![Quick Overview](assets/quick-overview.png)

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Tools](#tools)
- [Prompts](#prompts)
- [CLI](#cli)
- [Local Agent](#local-agent)
- [Development](#development)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Community](#community)
- [License](#license)

## Overview

The Kubeflow MCP Server bridges AI assistants/agents with Kubeflow's training infrastructure. Instead of writing YAML manifests or learning Kubernetes APIs, simply describe what you want to train and let AI handle the complexity.

### Key Benefits

- **Natural Language Interface**: Describe training jobs in plain English — "fine-tune Llama-3 on my dataset with 4 GPUs"
- **Smart Resource Planning**: AI estimates GPU/memory requirements before job submission
- **Real-time Monitoring**: Stream logs, track progress, and debug failures conversationally
- **Safe by Design**: Preview configurations before submission, built-in validation and guardrails
- **Multi-Client Support**: Works with Claude Desktop, Cursor IDE, MCP Inspector, or custom agents

### Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| **Kubeflow SDK** | ≥0.4.0 | TrainerClient API for training jobs |
| **Kubernetes** | ≥1.28 | With TrainJob CRD installed |
| **Python** | ≥3.10 | Async support required |

This MCP server wraps the [Kubeflow Training SDK](https://pypi.org/project/kubeflow/) `TrainerClient` API. All training operations (fine-tuning, custom scripts, container jobs) use SDK types like `BuiltinTrainer`, `CustomTrainer`, `TorchTuneConfig`, and `LoraConfig`.

## Quick Start

### Installation

```bash
pip install kubeflow-mcp
```

### Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "kubeflow": {
      "command": "kubeflow-mcp",
      "args": ["serve", "--persona", "ml-engineer"]
    }
  }
}
```

| Option | Values | Default |
|--------|--------|---------|
| `--persona` | `readonly`, `data-scientist`, `ml-engineer`, `platform-admin` | `ml-engineer` |
| `--transport` | `stdio`, `http` | `stdio` |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

<details>
<summary><b>Config file locations</b></summary>

| Client | Config Path |
|--------|-------------|
| **Cursor IDE** | `~/.cursor/mcp.json` |
| **Claude Desktop (macOS)** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Claude Desktop (Windows)** | `%APPDATA%\Claude\claude_desktop_config.json` |

</details>

<details>
<summary><b>Container deployment</b></summary>

```json
{
  "mcpServers": {
    "kubeflow": {
      "command": "podman",
      "args": [
        "run", "--rm", "-i",
        "-v", "${HOME}/.kube:/home/mcp/.kube:ro",
        "ghcr.io/kubeflow/mcp-server:latest",
        "serve"
      ]
    }
  }
}
```

Replace `podman` with `docker` if needed.
</details>

<details>
<summary><b>MCP Inspector (debugging)</b></summary>

```bash
npx @modelcontextprotocol/inspector uv run kubeflow-mcp serve
```
</details>

### Try It

```
"What training jobs are running in my cluster?"
"Fine-tune google/gemma-2b on squad dataset with 2 GPUs"
"Show me logs for the failed training job"
```

## Tools

| Category | Tools | Description |
|----------|-------|-------------|
| **Planning** | `get_cluster_resources`, `estimate_resources` | Check capacity, estimate requirements |
| **Training** | `fine_tune`, `run_custom_training`, `run_container_training` | Submit training jobs |
| **Discovery** | `list_training_jobs`, `get_training_job`, `list_runtimes`, `get_runtime` | Browse jobs and runtimes |
| **Monitoring** | `get_training_logs`, `get_training_events`, `wait_for_training` | Logs, events, status |
| **Lifecycle** | `delete_training_job`, `suspend_training_job`, `resume_training_job` | Manage job lifecycle |

<details>
<summary><b>Example: Fine-tune an LLM</b></summary>

```python
fine_tune(
    model="google/gemma-2b",
    dataset="squad",
    num_nodes=2,
    gpu_per_node=1,
    confirmed=True
)
```
</details>

<details>
<summary><b>Example: Resource Estimation</b></summary>

Ask: *"How much GPU memory do I need for Llama-3-70B?"*

```json
{
  "model": "meta-llama/Llama-3-70B",
  "parameters": "70B",
  "estimated_memory_gb": 140,
  "recommended_gpus": 4,
  "gpu_type": "A100-80GB"
}
```
</details>

## Prompts

MCP prompts provide structured guidance for common workflows. MCP clients can discover and use these prompts:

| Prompt | Description |
|--------|-------------|
| `fine_tuning_workflow` | Step-by-step guide for fine-tuning LLMs with LoRA |
| `custom_training_workflow` | Guide for custom scripts or container training |
| `troubleshooting_guide` | Diagnose and fix common job failures |
| `resource_planning` | Plan resources before training |
| `monitoring_workflow` | Monitor jobs and debug issues |

<details>
<summary><b>Using prompts in MCP clients</b></summary>

MCP clients that support prompts (like Claude Desktop) can list and invoke these prompts directly. The prompts provide detailed, parameterized guidance that helps ensure successful training operations.

Example with parameters:

```
fine_tuning_workflow(model="meta-llama/Llama-3.2-3B", dataset="tatsu-lab/alpaca")
```
</details>

## Resources

MCP resources provide read-only reference data that clients can fetch without consuming tool calls:

| Resource URI | Content |
|--------------|---------|
| `trainer://models/supported` | Tested model configurations with GPU requirements |
| `trainer://runtimes/info` | Runtime documentation and patches |
| `trainer://guides/quickstart` | Quick start guide for new users |
| `trainer://guides/troubleshooting` | Troubleshooting quick reference |

## CLI

```bash
# Server
kubeflow-mcp serve                              # Start MCP server
kubeflow-mcp serve --clients trainer            # Specify client
kubeflow-mcp serve --persona ml-engineer        # Set persona
kubeflow-mcp status                             # Show server status

# Agent
kubeflow-mcp agent --backend ollama --model qwen3:8b
kubeflow-mcp agent --backend ollama --mode progressive
kubeflow-mcp agent --backend ollama --thinking  # Enable thinking output
```

## Local Agent

Run a fully local AI agent with Ollama — no cloud APIs required:

```bash
pip install kubeflow-mcp[agents]
ollama pull qwen3:8b
kubeflow-mcp agent --backend ollama --model qwen3:8b
```

![Ollama Agent](assets/ollama-agent-tools.png)

<details>
<summary><b>Tool loading modes</b></summary>

| Mode | Description |
|------|-------------|
| `full` | All tools via MCP protocol (default) |
| `progressive` | 3 meta-tools for hierarchical discovery |
| `semantic` | 2 meta-tools with embedding-based search |

```bash
kubeflow-mcp agent --backend ollama                    # Full mode (default)
kubeflow-mcp agent --backend ollama --mode progressive # Hierarchical discovery
kubeflow-mcp agent --backend ollama --mode semantic    # requires sentence-transformers
```

**Full mode** connects via the standard MCP stdio protocol, identical to Cursor and Claude Desktop.
</details>

<details>
<summary><b>Recommended models</b></summary>

| Model | Context | RAM | Tool Calling |
|-------|---------|-----|--------------|
| `qwen3:8b` | 32K | 8GB | ✅ |
| `qwen2.5:7b` | 32K | 7GB | ✅ |
| `llama3.2:3b` | 8K | 3GB | ✅ |

For 8K context models, use `--mode progressive` or `--mode semantic`.
</details>

<details>
<summary><b>Agent commands</b></summary>

| Command | Description |
|---------|-------------|
| `/tools` | List available tools |
| `/mode [name]` | Switch tool mode |
| `/file <path>` | Read and analyze a file |
| `/clear` | Clear conversation |
| `exit` | Quit |
</details>

## Development

```bash
make dev           # Install dev dependencies
make check         # Lint + type check
make test          # Run tests
make pre-commit    # All checks before commit
```

See `make help` for all commands. For detailed setup, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Roadmap

| Component | Status | Description |
|-----------|--------|-------------|
| **TrainerClient** | ✅ Available | 16 training tools |
| **OptimizerClient** | 🔲 Planned | Katib hyperparameter tuning |
| **ModelRegistryClient** | 🔲 Planned | Model versioning |

See [ROADMAP.md](ROADMAP.md) for details.

## Contributing

```bash
git clone https://github.com/kubeflow/mcp-server.git
cd mcp-server
make dev && make pre-commit
```

Look for [`good first issue`](https://github.com/kubeflow/mcp-server/labels/good%20first%20issue) labels.

| Doc | Description |
|-----|-------------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guidelines, DCO, code style |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, testing |
| [SECURITY.md](SECURITY.md) | Security policy |

## Community

- **Slack**: [#wg-training](https://kubeflow.slack.com) on Kubeflow Slack
- **Meetings**: [Kubeflow SDK and ML Experience](https://bit.ly/kf-ml-experience) bi-weekly

## License

Apache-2.0

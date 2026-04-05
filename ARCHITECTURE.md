# Kubeflow MCP Server Architecture

## Overview

The MCP server acts as a translation layer between AI assistants and Kubeflow's training infrastructure.

```mermaid
flowchart TB
    subgraph Clients["MCP Clients"]
        Cursor[Cursor IDE]
        Claude[Claude Desktop]
        LocalAgent[Local Ollama Agent]
    end

    subgraph Server["kubeflow-mcp Server"]
        Instructions[SERVER_INSTRUCTIONS]
        Prompts[5 MCP Prompts]
        Resources[4 MCP Resources]
        Tools[16 Tools]
        Policy[Persona Policies]
        
        subgraph Modules["Modules"]
            Trainer[trainer - implemented]
            Optimizer[katib - optimizer - stub ]
            Hub[model-registry - hub - stub ]
        end
        
        Instructions --> Tools
        Prompts --> Tools
        Resources -.-> Prompts
        Policy --> Tools
    end

    subgraph Backend["Backend"]
        SDK[Kubeflow SDK]
        K8s[Kubernetes Cluster]
        SDK --> K8s
    end

    Cursor -->|MCP stdio| Server
    Claude -->|MCP stdio| Server
    LocalAgent -->|MCP stdio| Server
    Server -->|Python API| SDK
```

**All clients connect via the same MCP stdio protocol**, ensuring consistent behavior and access to tools, prompts, and server instructions.

## Module Structure

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `core/` | Server infrastructure | `server.py`, `prompts.py`, `resources.py`, `policy.py`, `config.py`, `security.py`, `resilience.py` |
| `trainer/` | Kubeflow Training tools | `api/planning.py`, `api/training.py`, `api/discovery.py`, `api/monitoring.py`, `api/lifecycle.py` |
| `agents/` | Local agent implementations | `ollama.py`, `dynamic_tools.py`, `mcp_client.py` |
| `optimizer/` | Katib integration | Stub for Phase 2 |
| `hub/` | Model Registry integration | Stub for Phase 3 |
| `common/` | Shared utilities | `types.py`, `constants.py`, `utils.py` |

## Tool Categories

Tools are organized by workflow stage:

| Category | Purpose | Tools |
|----------|---------|-------|
| **planning** | Check resources before training | `get_cluster_resources`, `estimate_resources` |
| **training** | Submit training jobs | `fine_tune`, `run_custom_training`, `run_container_training` |
| **discovery** | Find jobs and runtimes | `list_training_jobs`, `get_training_job`, `list_runtimes`, `get_runtime`, `get_runtime_packages` |
| **monitoring** | Track job progress | `get_training_logs`, `get_training_events`, `wait_for_training` |
| **lifecycle** | Manage running jobs | `delete_training_job`, `suspend_training_job`, `resume_training_job` |

## Workflow & Prompts

### Critical Workflow (SERVER_INSTRUCTIONS)

All clients receive the same workflow guidance via `SERVER_INSTRUCTIONS`:

```mermaid
flowchart LR
    subgraph Phase1["1. PLANNING"]
        A1[get_cluster_resources]
        A2[estimate_resources]
    end
    
    subgraph Phase2["2. DISCOVERY"]
        B1[list_runtimes]
        B2[list_training_jobs]
    end
    
    subgraph Phase3["3. TRAINING"]
        C1[Preview: confirmed=False]
        C2[Submit: confirmed=True]
    end
    
    subgraph Phase4["4. MONITORING"]
        D1[get_training_job]
        D2[get_training_logs]
        D3[get_training_events]
    end
    
    Phase1 --> Phase2 --> Phase3 --> Phase4
```

### MCP Prompts (On-Demand Guidance)

Prompts provide detailed, parameterized guidance without bloating the system prompt:

| Prompt | Parameters | Purpose |
|--------|------------|---------|
| `fine_tuning_workflow` | `model`, `dataset` | Step-by-step LLM fine-tuning guide |
| `custom_training_workflow` | `training_type` | Script or container training guide |
| `troubleshooting_guide` | `error_type` | Diagnose OOM, pending, image pull, NCCL errors |
| `resource_planning` | `model` | GPU memory and batch size recommendations |
| `monitoring_workflow` | `job_name` | Monitor progress and debug failures |

### MCP Resources (Read-Only Reference Data)

Resources provide cacheable, read-only data that clients can fetch without consuming tool call quota:

| Resource URI | Content |
|--------------|---------|
| `trainer://models/supported` | Tested model configurations with GPU requirements |
| `trainer://runtimes/info` | Runtime documentation and usage |
| `trainer://guides/quickstart` | Quick start guide for new users |
| `trainer://guides/troubleshooting` | Troubleshooting quick reference |

### Tool Tags (Phase-Based Discovery)

Tools include `tags` in their annotations for phase-based discovery:

| Tag | Phase | Tools |
|-----|-------|-------|
| `planning` | 1 | `get_cluster_resources`, `estimate_resources` |
| `discovery` | 2 | `list_*`, `get_runtime*` |
| `training` | 3 | `fine_tune`, `run_custom_training`, `run_container_training` |
| `monitoring` | 4 | `get_training_logs`, `get_training_events`, `wait_for_training` |
| `lifecycle` | - | `delete_*`, `suspend_*`, `resume_*` |

### Fine-Tuning Workflow Sequence

```mermaid
sequenceDiagram
    participant User
    participant AI as AI Client
    participant MCP as kubeflow-mcp
    participant K8s as Kubernetes

    User->>AI: "Fine-tune Llama-3.2-3B on alpaca"
    
    Note over AI: Reads SERVER_INSTRUCTIONS<br/>Follows 4-phase workflow
    
    rect rgb(230, 245, 255)
        Note over AI,MCP: Phase 1: PLANNING
        AI->>MCP: get_cluster_resources()
        MCP-->>AI: {gpu_total: 2, nodes_with_gpu: 1}
        AI->>MCP: estimate_resources("Llama-3.2-3B")
        MCP-->>AI: {gpu_memory: "16GB", batch_size: 4}
    end
    
    rect rgb(230, 255, 230)
        Note over AI,MCP: Phase 2: DISCOVERY
        AI->>MCP: list_runtimes()
        MCP-->>AI: {runtimes: ["torch-tune"]}
    end
    
    rect rgb(255, 245, 230)
        Note over AI,MCP: Phase 3: TRAINING (Preview)
        AI->>MCP: fine_tune(..., confirmed=False)
        MCP-->>AI: {status: "preview", config: {...}}
        AI->>User: "Here's the config. Proceed?"
        User->>AI: "Yes"
        AI->>MCP: fine_tune(..., confirmed=True)
        MCP->>K8s: Create TrainJob CRD
        K8s-->>MCP: Job created
        MCP-->>AI: {job_name: "trainjob-abc123"}
    end
    
    rect rgb(255, 230, 245)
        Note over AI,MCP: Phase 4: MONITORING
        AI->>MCP: get_training_logs("trainjob-abc123")
        MCP->>K8s: Get pod logs
        K8s-->>MCP: Logs
        MCP-->>AI: {logs: "Epoch 1/3: loss=2.34..."}
        AI->>User: "Training in progress..."
    end
```

### Error Recovery with Hints

When tools return errors, they include hints pointing to relevant prompts:

```mermaid
flowchart TD
    A[Tool Call] --> B{Success?}
    B -->|Yes| C[ToolResponse]
    B -->|No| D[ToolError + hint]
    
    D --> E{Error Type}
    E -->|SDK Error| F["hint: troubleshooting_guide"]
    E -->|Script Validation| G["hint: custom_training_workflow"]
    E -->|Job Not Found| H["hint: list_training_jobs"]
    E -->|Timeout| I["hint: get_training_events"]
    
    F --> J[AI requests prompt]
    G --> J
    H --> J
    I --> J
    
    J --> K[Detailed recovery steps]
```

| Error Type | Hint | Recovery Action |
|------------|------|-----------------|
| Training SDK errors | `troubleshooting_guide`, `resource_planning` | Diagnose, check resources |
| Script validation failed | `custom_training_workflow` | Fix script or use container |
| Job not found | `list_training_jobs` | Find correct job name |
| Monitoring failures | `monitoring_workflow` | Step-by-step debugging |
| Timeout | `get_training_events` | Check K8s scheduling |

### Client Consistency

All clients connect via the same MCP stdio protocol:

```mermaid
flowchart TB
    subgraph Source["Single Source of Truth"]
        SI[SERVER_INSTRUCTIONS]
        PR[MCP Prompts]
        TL[Tools]
    end
    
    subgraph Clients["All via MCP stdio"]
        C1[Cursor IDE]
        C2[Claude Desktop]
        C3[Local Ollama Agent]
    end
    
    SI --> C1
    SI --> C2
    SI --> C3
    
    PR -.->|on-demand| C1
    PR -.->|on-demand| C2
    PR -.->|on-demand| C3
    
    TL --> C1
    TL --> C2
    TL --> C3
```

| Client | Protocol | Tools | Instructions | Prompts |
|--------|----------|-------|--------------|---------|
| Cursor IDE | MCP stdio | MCP protocol | `SERVER_INSTRUCTIONS` | MCP prompts API |
| Claude Desktop | MCP stdio | MCP protocol | `SERVER_INSTRUCTIONS` | MCP prompts API |
| Local Agent (full) | MCP stdio | MCP protocol | `SERVER_INSTRUCTIONS` | MCP prompts API |
| Local Agent (progressive/semantic) | Direct | Meta-tools | Dynamic prompt | Not available |

The default `--mode full` uses the standard MCP protocol, ensuring identical behavior across all clients.

## Token-Efficient Modes

To reduce LLM context usage, three tool loading modes are supported:

| Mode | Initial Tokens | Reduction | Mechanism |
|------|---------------|-----------|-----------|
| **Full** | ~900 | baseline | All tools via MCP protocol |
| **Progressive** | ~85 | -91% | 3 meta-tools with hierarchical discovery |
| **Semantic** | ~69 | -92% | 2 meta-tools with embedding-based search |

Note: `static` and `mcp` are legacy aliases for `full` mode.

## Access Control

### Persona-Based Filtering

| Persona | Access Level | Tools |
|---------|--------------|-------|
| `readonly` | View only | `list_*`, `get_*` |
| `data-scientist` | + Training | `fine_tune`, `run_custom_training`, `delete_training_job` |
| `ml-engineer` | + Lifecycle | `run_container_training`, `suspend_*`, `resume_*` |
| `platform-admin` | Unrestricted | All tools |

### Policy-Based Filtering

Custom policies in `~/.kf-mcp-policy.yaml` can further restrict access:
- **allow**: Whitelist tools or categories
- **deny**: Blacklist tools or risk levels (e.g., `risk:destructive`)
- **namespaces**: Restrict to specific Kubernetes namespaces

## Preview-Before-Submit Pattern

Training tools use a two-phase confirmation to prevent accidental resource consumption:

| Phase | Call | Returns |
|-------|------|---------|
| 1. Preview | `fine_tune(..., confirmed=False)` | `{"status": "preview", "config": {...}}` |
| 2. Submit | `fine_tune(..., confirmed=True)` | `{"success": True, "job_name": "..."}` |

## Extension Points

### Adding a New Tool

1. Create function in appropriate `api/*.py` module
2. Add to `TOOLS` list in `trainer/__init__.py`
3. Add to `TOOL_CATEGORIES` dict
4. Add annotations in `core/server.py`
5. Write unit tests

### Adding a New Client Module

1. Create `src/kubeflow_mcp/newclient/` directory
2. Implement tools in `api/` subdirectory
3. Export `TOOLS` list in `__init__.py`
4. Register in `core/server.py` `CLIENT_MODULES`
5. Add optional dependency in `pyproject.toml`

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant MCP Client
    participant kubeflow-mcp
    participant Kubeflow SDK
    participant Kubernetes

    User->>MCP Client: Natural language request
    MCP Client->>kubeflow-mcp: JSON-RPC tool call
    kubeflow-mcp->>Kubeflow SDK: Python method call
    Kubeflow SDK->>Kubernetes: CRD operations
    Kubernetes-->>Kubeflow SDK: Response
    Kubeflow SDK-->>kubeflow-mcp: Result
    kubeflow-mcp-->>MCP Client: JSON response
    MCP Client-->>User: Formatted output
```

## Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development setup
- [README.md](README.md) - User documentation
- [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/training/)

---
name: Kubeflow Trainer
description: AI-powered interface for distributed training and LLM fine-tuning on Kubernetes
globs:
  - "src/kubeflow_mcp/trainer/**/*.py"
  - "tests/**/trainer/**/*.py"
---

# Kubeflow Trainer Skill

AI-powered interface for distributed training and LLM fine-tuning on Kubernetes.

## When to Use This Skill

Use this skill when the user wants to:
- Fine-tune LLMs (Llama, Mistral, Gemma, etc.)
- Run distributed training jobs on Kubernetes
- Monitor training progress and debug failures
- Manage training job lifecycle (suspend, resume, delete)

## Available Tools

### Planning (call first)

| Tool | Purpose |
|------|---------|
| `get_cluster_resources` | Check GPU availability before training |
| `estimate_resources` | Get resource requirements for a model |

### Training (requires confirmation)

| Tool | Purpose |
|------|---------|
| `fine_tune` | Fine-tune HuggingFace models with LoRA |
| `run_custom_training` | Run user-provided Python scripts |
| `run_container_training` | Run pre-built container images |

### Discovery

| Tool | Purpose |
|------|---------|
| `list_training_jobs` | List all training jobs |
| `get_training_job` | Get job details |
| `list_runtimes` | List available training runtimes |
| `get_runtime` | Get runtime configuration |

### Monitoring

| Tool | Purpose |
|------|---------|
| `get_training_logs` | View worker logs |
| `get_training_events` | View K8s events |
| `wait_for_training` | Wait for job completion |

### Lifecycle

| Tool | Purpose |
|------|---------|
| `delete_training_job` | Delete a job |
| `suspend_training_job` | Pause a running job |
| `resume_training_job` | Resume a suspended job |

## Standard Workflows

### Fine-Tuning Workflow

1. `get_cluster_resources()` - Check available GPUs/nodes
2. `estimate_resources(model)` - Check what the model needs
3. `list_runtimes()` - Check available training runtimes
4. `fine_tune(..., confirmed=False)` - Preview the job config
5. User reviews and approves
6. `fine_tune(..., confirmed=True)` - Submit the job
7. `get_training_logs()` or `wait_for_training()` - Monitor progress

### Debugging Workflow

1. `list_training_jobs(status="Failed")` - Find failed jobs
2. `get_training_job(name)` - Check status
3. `get_training_events(name)` - Check K8s events
4. `get_training_logs(name)` - Read error logs

## Key Patterns

### Two-Phase Confirmation

All mutation tools require `confirmed=True` to execute:

- Step 1: Preview (confirmed=False by default)
- Step 2: Execute after user approval (confirmed=True)

### Resource Estimation First

Always call `estimate_resources()` before `fine_tune()` to get recommended GPU and memory settings.

### Runtime Patches

Customize runtime behavior when submitting jobs:

```python
fine_tune(
    model="hf://google/gemma-2b",
    dataset="hf://tatsu-lab/alpaca",
    # Target specific GPU nodes
    node_selector={"node-type": "gpu-a100"},
    # Schedule on tainted GPU nodes
    tolerations=[{"key": "nvidia.com/gpu", "operator": "Exists"}],
    # Add environment variables
    env=[{"name": "NCCL_DEBUG", "value": "INFO"}],
    # Mount a PVC for checkpoints
    volumes=[{"name": "ckpt", "persistentVolumeClaim": {"claimName": "my-pvc"}}],
    volume_mounts=[{"name": "ckpt", "mountPath": "/checkpoints"}],
    confirmed=True
)
```

| Patch Option | Purpose |
|--------------|---------|
| `node_selector` | Target specific nodes (e.g., GPU type) |
| `tolerations` | Schedule on tainted nodes |
| `env` | Add environment variables |
| `volumes` | Add PVC/ConfigMap/Secret volumes |
| `volume_mounts` | Mount volumes to containers |

## Token-Efficient Tool Modes (Ollama Agent)

The Ollama agent supports dynamic tool loading for context-limited models:

| Mode | Tools | Tokens | Use Case |
|------|-------|--------|----------|
| `static` | 16 | ~2,100 | Full access (32K context) |
| `lite` | 5 core | ~710 | Limited context (8K) |
| `progressive` | 3 meta | ~680 | Hierarchical discovery |
| `semantic` | 2 meta | ~430 | Natural language search |

### Progressive Discovery (3 meta-tools)

```
list_tools(prefix) → describe_tools([names]) → execute_tool(name, args)
```

Example: `list_tools("training")` → `describe_tools(["fine_tune"])` → `execute_tool("fine_tune", {...})`

### Semantic Search (2 meta-tools)

```
find_tools(query) → execute_tool(name, args)
```

Example: `find_tools("fine-tune a model")` → `execute_tool("fine_tune", {...})`

## Common Issues

| Issue | Solution |
|-------|----------|
| No GPUs available | Check `get_cluster_resources()`, wait or request more |
| Image pull failed | Check image name, verify imagePullSecrets |
| OOMKilled | Reduce batch_size or increase memory |
| Job stuck Pending | Check events with `get_training_events()` |
| Runtime not found | Call `list_runtimes()` to see available options |
| Context overflow | Use `--mode lite` or `--mode progressive` |

## Related Skills

- `@skills/trainer/fine-tuning.md` - Detailed fine-tuning guide
- `@skills/trainer/custom-training.md` - Custom script guide
- `@skills/trainer/troubleshooting.md` - Error recovery

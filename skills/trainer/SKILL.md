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

1. `get_cluster_resources()` - Verify GPUs available
2. `estimate_resources(model)` - Get recommended settings
3. `fine_tune(..., confirmed=False)` - Preview config
4. User reviews and approves
5. `fine_tune(..., confirmed=True)` - Submit job
6. `wait_for_training()` or `get_training_logs()` - Monitor

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

## Common Issues

| Issue | Solution |
|-------|----------|
| No GPUs available | Check `get_cluster_resources()`, wait or request more |
| Image pull failed | Check image name, verify imagePullSecrets |
| OOMKilled | Reduce batch_size or increase memory |
| Job stuck Pending | Check events with `get_training_events()` |

## Related Skills

- `@skills/trainer/fine-tuning.md` - Detailed fine-tuning guide
- `@skills/trainer/custom-training.md` - Custom script guide
- `@skills/trainer/troubleshooting.md` - Error recovery

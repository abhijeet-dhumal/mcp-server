# Fine-Tuning Workflow

Step-by-step guide for fine-tuning HuggingFace models with Kubeflow.

## Prerequisites

- Kubernetes cluster with GPUs
- HuggingFace token (for gated models like Llama)
- Dataset on HuggingFace Hub

## Step 1: Check Cluster Resources

Call `get_cluster_resources()` to verify GPUs are available.

If no GPUs: Wait for resources or contact cluster admin.

## Step 2: Estimate Requirements

Call `estimate_resources(model, num_workers, batch_size)` to get recommended settings.

## Step 3: Preview Configuration

Call `fine_tune(..., confirmed=False)` to preview the configuration.

Review the config before proceeding.

## Step 4: Submit Training Job

After user confirmation, call `fine_tune(..., confirmed=True)` to execute.

## Step 5: Monitor Progress

Option A: `wait_for_training(name, target_status="Succeeded")`
Option B: `get_training_logs(name, tail_lines=50)` periodically

## Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `model` | HuggingFace model path | Required |
| `dataset` | HuggingFace dataset path | Required |
| `num_workers` | Parallel training workers | 1 |
| `gpu_per_worker` | GPUs per worker | 1 |
| `epochs` | Training epochs | 3 |
| `batch_size` | Per-device batch size | 4 |
| `learning_rate` | Learning rate | 2e-5 |
| `lora` | Use LoRA (efficient) | True |

## Model-Specific Settings

### Llama 3.2 (1B)
- gpu_per_worker: 1
- batch_size: 4
- lora: True

### Llama 3.1 (8B)
- gpu_per_worker: 2
- batch_size: 2
- lora: True

### Llama 3.1 (70B)
- num_workers: 2
- gpu_per_worker: 4
- batch_size: 1
- lora: True

## Troubleshooting

### HF_TOKEN not set
Gated models (Llama) require authentication. Set HF_TOKEN environment variable.

### OOMKilled
- Reduce `batch_size`
- Enable `lora=True` (uses less memory)
- Increase `gpu_per_worker`

### Slow training
- Increase `num_workers` for data parallelism
- Increase `batch_size` if memory allows

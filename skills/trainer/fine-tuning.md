# Fine-Tuning LLMs with Kubeflow

Detailed guide for fine-tuning models using the `fine_tune()` tool. Wraps the Kubeflow SDK's `TrainerClient.train()` with `BuiltinTrainer` (TorchTune).

## Prerequisites

Before fine-tuning, verify:

1. **GPU availability**: `get_cluster_resources()` must show `gpu_total > 0`
2. **Runtime installed**: `list_runtimes()` should include `torch-tune`
3. **Model access**: For gated models (Llama, Mistral), you need an HF token

## Supported Models

The `fine_tune()` tool works with any model compatible with TorchTune:

| Model Family | Example ID | Min GPU Memory |
|--------------|------------|----------------|
| Gemma | `google/gemma-2b` | 8GB |
| Llama 3.2 | `meta-llama/Llama-3.2-1B` | 8GB |
| Llama 3.2 | `meta-llama/Llama-3.2-3B` | 16GB |
| Llama 3.1 | `meta-llama/Llama-3.1-8B` | 24GB |
| Mistral | `mistralai/Mistral-7B-v0.1` | 24GB |
| Qwen | `Qwen/Qwen2.5-7B-Instruct` | 24GB |

## Data Sources

### HuggingFace Hub (Default)

Use `hf://` prefix for HuggingFace datasets and models:

```python
fine_tune(
    model="hf://google/gemma-2b",
    dataset="hf://tatsu-lab/alpaca",
    ...
)
```

### S3 Storage

The SDK also supports S3 via `S3ModelInitializer` and `S3DatasetInitializer` (requires custom training for now).

## Dataset Formats

### Instruction Format (Alpaca-style)
```json
{"instruction": "Summarize this text", "input": "Long article...", "output": "Summary..."}
```

### Chat Format
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### Popular Datasets
- `tatsu-lab/alpaca` - General instruction following
- `databricks/dolly-15k` - Diverse instructions
- `OpenAssistant/oasst1` - Conversational
- `squad` - Question answering

## Step-by-Step Workflow

### Step 1: Check Resources

```python
get_cluster_resources()
# Returns: {gpu_total: 4, nodes_with_gpu: 2, ...}
```

If `gpu_total = 0`, you cannot fine-tune. Request GPU nodes first.

### Step 2: Estimate Requirements

```python
estimate_resources(model="meta-llama/Llama-3.2-3B", batch_size=4)
# Returns: {gpu_memory_required: "16GB", gpu_type_recommended: "16GB (T4/RTX 4080)"}
```

Compare with available resources from Step 1.

### Step 3: Preview Configuration

```python
fine_tune(
    model="hf://meta-llama/Llama-3.2-3B",
    dataset="hf://tatsu-lab/alpaca",
    batch_size=4,
    epochs=1,
    confirmed=False  # Preview only
)
# Returns: {status: "preview", config: {...}}
```

Review the configuration before submitting.

### Step 4: Submit Job

```python
fine_tune(
    model="hf://meta-llama/Llama-3.2-3B",
    dataset="hf://tatsu-lab/alpaca",
    batch_size=4,
    epochs=1,
    confirmed=True  # Actually submit
)
# Returns: {job_name: "trainjob-abc123", status: "Created"}
```

### Step 5: Monitor Progress

```python
get_training_logs(name="trainjob-abc123")
# Returns: {logs: "Epoch 1/3: loss=2.34...", lines: 150}
```

Or wait for completion:

```python
wait_for_training(name="trainjob-abc123", timeout_seconds=3600)
```

## Parameter Tuning Guide

### Batch Size

| GPU Memory | Recommended batch_size |
|------------|----------------------|
| 8GB | 1-2 |
| 16GB | 2-4 |
| 24GB | 4-8 |
| 40GB+ | 8-16 |

If you get OOMKilled, reduce batch_size.

### LoRA Parameters

The SDK's `LoraConfig` supports these parameters:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `lora_rank` | 8 | Higher = more capacity, more memory |
| `lora_alpha` | 16 | Scaling factor, typically 2x rank |
| `lora_dropout` | 0.0 | Dropout on LoRA layers (regularization) |
| `quantize_base` | False | Enable 4-bit quantization (QLoRA) |
| `use_dora` | False | Use DoRA (Weight-Decomposed LoRA) |
| `apply_lora_to_mlp` | False | Apply LoRA to MLP layers |
| `apply_lora_to_output` | False | Apply LoRA to output projection |
| `lora_attn_modules` | `["q_proj", "v_proj", "output_proj"]` | Which attention layers to adapt |

For most use cases, defaults work well. Increase rank for complex tasks.

### QLoRA (4-bit Quantization)

For memory-constrained setups, enable quantization:

```python
# Via custom training (SDK supports quantize_base in LoraConfig)
# This reduces memory by ~4x but requires bitsandbytes
```

### Epochs

- **1 epoch**: Quick test, may underfit
- **2-3 epochs**: Good for most datasets
- **5+ epochs**: Risk of overfitting on small datasets

## Gated Models (Llama, Mistral)

For models requiring authentication:

```python
fine_tune(
    model="hf://meta-llama/Llama-3.2-3B",
    dataset="hf://tatsu-lab/alpaca",
    hf_token="hf_xxxxx",  # Your HuggingFace token
    confirmed=True
)
```

Get your token from: https://huggingface.co/settings/tokens

## Multi-Node Training

For large models or faster training:

```python
fine_tune(
    model="hf://meta-llama/Llama-3.1-8B",
    dataset="hf://tatsu-lab/alpaca",
    num_nodes=2,  # Distribute across 2 nodes
    confirmed=True
)
```

Requirements:
- Nodes must have same GPU type
- Network bandwidth between nodes matters
- Use for models > 7B parameters

## Saving Checkpoints

Mount a PVC to save model checkpoints:

```python
fine_tune(
    model="hf://google/gemma-2b",
    dataset="hf://tatsu-lab/alpaca",
    volumes=[{
        "name": "checkpoints",
        "persistentVolumeClaim": {"claimName": "training-checkpoints"}
    }],
    volume_mounts=[{
        "name": "checkpoints",
        "mountPath": "/output"
    }],
    confirmed=True
)
```

Checkpoints are saved to `/output` inside the container.

## Targeting Specific GPUs

Use node selectors to target specific GPU types:

```python
fine_tune(
    model="hf://meta-llama/Llama-3.1-8B",
    dataset="hf://tatsu-lab/alpaca",
    node_selector={"nvidia.com/gpu.product": "NVIDIA-A100-SXM4-80GB"},
    tolerations=[{"key": "nvidia.com/gpu", "operator": "Exists"}],
    confirmed=True
)
```

Common GPU labels:
- `nvidia.com/gpu.product`: GPU model name
- `node-type`: Custom label (cluster-specific)

## Common Patterns

### Quick Test (Small Model)
```python
fine_tune(
    model="hf://google/gemma-2b",
    dataset="hf://tatsu-lab/alpaca",
    batch_size=2,
    epochs=1,
    confirmed=True
)
```

### Production Fine-Tuning
```python
fine_tune(
    model="hf://meta-llama/Llama-3.1-8B",
    dataset="hf://your-org/custom-dataset",
    hf_token="hf_xxxxx",
    batch_size=4,
    epochs=3,
    num_nodes=2,
    lora_rank=16,
    lora_alpha=32,
    node_selector={"node-type": "gpu-a100"},
    volumes=[{"name": "ckpt", "persistentVolumeClaim": {"claimName": "checkpoints"}}],
    volume_mounts=[{"name": "ckpt", "mountPath": "/output"}],
    confirmed=True
)
```

## What Happens Internally

1. **Model Download**: HuggingFace model downloaded to init container
2. **Dataset Download**: Dataset downloaded and preprocessed
3. **Training**: TorchTune runs LoRA fine-tuning
4. **Checkpoints**: Model weights saved periodically

The SDK creates a TrainJob CRD that orchestrates these steps.

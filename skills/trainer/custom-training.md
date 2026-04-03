# Custom Training Scripts

Guide for running user-provided Python training scripts with `run_custom_training()` and container images with `run_container_training()`.

These tools wrap the Kubeflow SDK's `TrainerClient.train()` with:
- `CustomTrainer` - For Python functions
- `CustomTrainerContainer` - For pre-built container images

## When to Use Custom Training

Use custom training instead of `fine_tune()` when:

- You have a custom training loop
- You need frameworks other than TorchTune (e.g., TRL, Axolotl, Unsloth)
- You want full control over the training process
- You're training non-LLM models
- You need S3 data sources (SDK supports `S3DatasetInitializer`)

## run_custom_training()

Runs your Python script on the cluster. The script is validated for security and executed in a container.

### Basic Usage

```python
script = """
import torch
import torch.distributed as dist

dist.init_process_group(backend='nccl')
rank = dist.get_rank()
print(f"Hello from rank {rank}")

# Your training code here
model = torch.nn.Linear(10, 10).cuda()
optimizer = torch.optim.Adam(model.parameters())

for epoch in range(10):
    loss = model(torch.randn(32, 10).cuda()).sum()
    loss.backward()
    optimizer.step()
    if rank == 0:
        print(f"Epoch {epoch}: loss={loss.item():.4f}")
"""

run_custom_training(
    script=script,
    num_nodes=2,
    gpu_per_node=1,
    packages=["torch"],
    confirmed=True
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `script` | str | Python code to execute |
| `name` | str | Job name (auto-generated if omitted) |
| `num_nodes` | int | Number of distributed nodes (default: 1) |
| `gpu_per_node` | int | GPUs per node (default: 1, use 0 for CPU) |
| `packages` | list[str] | Pip packages to install |
| `confirmed` | bool | Must be True to submit |

### Script Requirements

Your script should:

1. **Initialize distributed** (if multi-node):
   ```python
   import torch.distributed as dist
   dist.init_process_group(backend='nccl')
   ```

2. **Handle rank correctly**:
   ```python
   rank = dist.get_rank()
   world_size = dist.get_world_size()
   ```

3. **Use CUDA if GPU requested**:
   ```python
   device = torch.device(f"cuda:{local_rank}")
   model = model.to(device)
   ```

### Security Restrictions

The following are **not allowed** in scripts:

- `import os`, `import subprocess`, `import sys`
- `eval()`, `exec()`, `compile()`, `open()`
- `__import__()`, `shutil`

If you need system access, use `run_container_training()` instead.

### Installing Packages

Specify pip packages to install:

```python
run_custom_training(
    script="from transformers import ...",
    packages=[
        "transformers>=4.40",
        "accelerate",
        "peft",
        "bitsandbytes",
    ],
    confirmed=True
)
```

## run_container_training()

Runs a pre-built container image. Use this for:

- Complex environments
- Private/proprietary code
- Full system access
- Production workloads

### Basic Usage

```python
run_container_training(
    image="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime",
    num_nodes=1,
    gpu_per_node=2,
    env={"LEARNING_RATE": "0.001"},
    confirmed=True
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | str | Container image URI |
| `command` | list[str] | Override entrypoint (optional) |
| `num_nodes` | int | Distributed nodes (default: 1) |
| `gpu_per_node` | int | GPUs per node (default: 1) |
| `env` | dict | Environment variables |
| `node_selector` | dict | Target specific nodes |
| `tolerations` | list | Schedule on tainted nodes |
| `volumes` | list | Mount PVCs/ConfigMaps |
| `volume_mounts` | list | Volume mount paths |
| `confirmed` | bool | Must be True to submit |

### Using Private Images

For private registries, ensure imagePullSecrets are configured in the namespace:

```python
run_container_training(
    image="ghcr.io/myorg/trainer:v1.0",
    confirmed=True
)
```

### Mounting Data

Mount a PVC with your training data:

```python
run_container_training(
    image="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime",
    volumes=[{
        "name": "data",
        "persistentVolumeClaim": {"claimName": "training-data"}
    }],
    volume_mounts=[{
        "name": "data",
        "mountPath": "/data"
    }],
    confirmed=True
)
```

### Environment Variables

Pass configuration via environment:

```python
run_container_training(
    image="myorg/trainer:latest",
    env={
        "MODEL_NAME": "llama-7b",
        "BATCH_SIZE": "8",
        "LEARNING_RATE": "2e-5",
        "WANDB_API_KEY": "xxx",  # For experiment tracking
    },
    confirmed=True
)
```

## Distributed Training Patterns

### PyTorch DDP (Multi-GPU, Single Node)

```python
script = """
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

dist.init_process_group(backend='nccl')
local_rank = int(os.environ['LOCAL_RANK'])
torch.cuda.set_device(local_rank)

model = YourModel().cuda()
model = DDP(model, device_ids=[local_rank])

# Training loop
for batch in dataloader:
    loss = model(batch)
    loss.backward()
    optimizer.step()
"""

run_custom_training(
    script=script,
    num_nodes=1,
    gpu_per_node=4,  # 4 GPUs on one node
    packages=["torch"],
    confirmed=True
)
```

### PyTorch DDP (Multi-Node)

```python
run_custom_training(
    script=script,  # Same DDP script
    num_nodes=2,    # 2 nodes
    gpu_per_node=4, # 4 GPUs each = 8 total
    packages=["torch"],
    confirmed=True
)
```

Environment variables set automatically:
- `WORLD_SIZE`: Total processes
- `RANK`: Global rank
- `LOCAL_RANK`: Rank within node
- `MASTER_ADDR`: Coordinator address
- `MASTER_PORT`: Coordinator port

### DeepSpeed

```python
script = """
import deepspeed
import torch

model = YourModel()
optimizer = torch.optim.Adam(model.parameters())

model_engine, optimizer, _, _ = deepspeed.initialize(
    model=model,
    optimizer=optimizer,
    config={
        "train_batch_size": 32,
        "gradient_accumulation_steps": 4,
        "fp16": {"enabled": True},
        "zero_optimization": {"stage": 2}
    }
)

for batch in dataloader:
    loss = model_engine(batch)
    model_engine.backward(loss)
    model_engine.step()
"""

run_custom_training(
    script=script,
    num_nodes=2,
    gpu_per_node=4,
    packages=["deepspeed", "torch"],
    confirmed=True
)
```

### Hugging Face Accelerate

```python
script = """
from accelerate import Accelerator
from transformers import AutoModelForCausalLM, AutoTokenizer

accelerator = Accelerator()

model = AutoModelForCausalLM.from_pretrained("gpt2")
optimizer = torch.optim.AdamW(model.parameters())
dataloader = ...  # Your dataloader

model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)

for batch in dataloader:
    outputs = model(**batch)
    loss = outputs.loss
    accelerator.backward(loss)
    optimizer.step()
"""

run_custom_training(
    script=script,
    num_nodes=1,
    gpu_per_node=2,
    packages=["accelerate", "transformers", "torch"],
    confirmed=True
)
```

## CPU-Only Training

For CPU training (e.g., small models, testing):

```python
run_custom_training(
    script="print('Hello from CPU')",
    num_nodes=1,
    gpu_per_node=0,  # No GPUs
    confirmed=True
)
```

## Debugging Custom Scripts

### Test Locally First

Before submitting to cluster:

```bash
python your_script.py
```

### Check Logs

After submission:

```python
get_training_logs(name="your-job-name")
```

### Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | Missing package | Add to `packages` list |
| `CUDA out of memory` | GPU OOM | Reduce batch size or model size |
| `NCCL timeout` | Network issue | Check node connectivity |
| `Script validation failed` | Dangerous import | Use `run_container_training()` |

## Best Practices

1. **Start small**: Test with 1 node, 1 GPU first
2. **Use checkpointing**: Save model periodically
3. **Log metrics**: Print loss/accuracy for monitoring
4. **Handle failures**: Implement resume from checkpoint
5. **Pin versions**: Specify exact package versions

# Custom Training Workflow

Guide for running user-provided Python training scripts on Kubeflow.

## When to Use

Use `run_custom_training` when:
- You have a custom training script
- Fine-tuning templates don't fit your use case
- You need specific training logic

Use `run_container_training` when:
- You have a pre-built Docker image
- Dependencies are complex
- You need full environment control

## Custom Script Training

### Step 1: Prepare Script

Your script runs in a distributed environment with PyTorch:

```python
script = '''
import torch
import torch.distributed as dist
from transformers import AutoModelForCausalLM, Trainer

# Initialize distributed
dist.init_process_group(backend="nccl")
local_rank = int(os.environ.get("LOCAL_RANK", 0))
torch.cuda.set_device(local_rank)

# Your training code here
model = AutoModelForCausalLM.from_pretrained("gpt2")
# ... training logic ...

print("Training complete!")
'''
```

### Step 2: Submit Job

```python
run_custom_training(
    script=script,
    num_workers=2,
    gpu_per_worker=1,
    packages=["transformers", "datasets"],
    confirmed=False  # Preview first
)
```

### Step 3: Execute

After reviewing config:

```python
run_custom_training(
    script=script,
    num_workers=2,
    gpu_per_worker=1,
    packages=["transformers", "datasets"],
    confirmed=True
)
```

## Container Training

### Step 1: Prepare Image

Your container should:
- Have training code at entrypoint
- Support distributed training env vars
- Handle `RANK`, `WORLD_SIZE`, `LOCAL_RANK`

### Step 2: Submit Job

```python
run_container_training(
    image="myregistry/my-training:v1",
    num_workers=4,
    gpu_per_worker=2,
    command=["python", "train.py", "--epochs", "10"],
    env={"LEARNING_RATE": "1e-4"},
    confirmed=False
)
```

### Step 3: Execute

```python
run_container_training(
    image="myregistry/my-training:v1",
    num_workers=4,
    gpu_per_worker=2,
    command=["python", "train.py", "--epochs", "10"],
    env={"LEARNING_RATE": "1e-4"},
    confirmed=True
)
```

## Script Safety Rules

Scripts are validated before execution. **Forbidden:**
- `import os`, `import subprocess`, `import sys`
- `eval()`, `exec()`, `open()`, `compile()`
- `__import__`

**Allowed:**
- `import torch`, `import transformers`
- Standard ML libraries
- File I/O through proper APIs

## Environment Variables

Your script has access to:

| Variable | Description |
|----------|-------------|
| `RANK` | Global worker rank |
| `WORLD_SIZE` | Total workers |
| `LOCAL_RANK` | GPU index on this node |
| `MASTER_ADDR` | Coordinator address |
| `MASTER_PORT` | Coordinator port |

## Example: Distributed PyTorch

```python
script = '''
import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP

# Setup
dist.init_process_group(backend="nccl")
rank = dist.get_rank()
local_rank = int(os.environ["LOCAL_RANK"])
torch.cuda.set_device(local_rank)

# Model
model = nn.Linear(10, 10).cuda()
model = DDP(model, device_ids=[local_rank])

# Training loop
optimizer = torch.optim.Adam(model.parameters())
for epoch in range(10):
    # ... training ...
    if rank == 0:
        print(f"Epoch {epoch} complete")

dist.destroy_process_group()
'''

run_custom_training(
    script=script,
    num_workers=2,
    gpu_per_worker=1,
    confirmed=True
)
```

## Monitoring

Same as fine-tuning:

```python
# Check status
get_training_job(name="custom-train-xyz")

# View logs
get_training_logs(name="custom-train-xyz", worker="worker-0")

# Wait for completion
wait_for_training(name="custom-train-xyz")
```

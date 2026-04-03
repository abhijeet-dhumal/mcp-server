# Examples

Sample training scripts for use with Kubeflow MCP.

## MNIST Distributed Training

Distributed CNN training on MNIST with PyTorch DDP:

```bash
# Using the agent
kubeflow-mcp agent --backend ollama --model qwen3:8b
/file examples/mnist_train.py
"Train this on my cluster with 2 workers"
```

**Features:**
- PyTorch DistributedDataParallel (DDP)
- Automatic NCCL (GPU) or Gloo (CPU) backend
- DistributedSampler for data sharding
- torch.compile optimization (PyTorch 2.0+)

**Requirements:** `torch`, `torchvision`

## Script Structure

Training scripts should define a single function that Kubeflow can invoke:

```python
def train_mnist(num_epochs=3, batch_size=64, lr=0.01):
    import torch
    import torch.distributed as dist
    # ... training code ...
```

The function:
- Imports dependencies inside (for serialization)
- Handles distributed setup (`dist.init_process_group`)
- Uses `DistributedSampler` for data sharding
- Cleans up with `dist.destroy_process_group()`

## Usage with Kubeflow MCP

1. **Load and analyze:**
   ```
   /file examples/mnist_train.py
   ```

2. **Train on cluster:**
   ```
   "Train this with 2 workers and 1 GPU each"
   ```

3. **The agent will:**
   - Check cluster resources
   - Detect required packages
   - Create distributed TrainJob
   - Show preview for confirmation

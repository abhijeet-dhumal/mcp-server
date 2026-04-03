"""Distributed MNIST training script for Kubeflow.

This script is designed to work with Kubeflow's distributed training.
The training function can be used directly with run_custom_training().

Usage with Kubeflow MCP agent:
    /file examples/mnist_train.py
    "Train this on my cluster with 2 workers"
"""


def train_mnist(num_epochs=3, batch_size=64, lr=0.01, momentum=0.9):
    """Train a CNN on MNIST with PyTorch distributed.
    
    Args:
        num_epochs: Number of training epochs
        batch_size: Batch size per worker
        lr: Learning rate
        momentum: SGD momentum
    """
    import os

    import torch
    import torch.distributed as dist
    import torch.nn.functional as F
    from torch import nn
    from torch.utils.data import DataLoader, DistributedSampler
    from torchvision import datasets, transforms

    # Define the PyTorch CNN model
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.conv1 = nn.Conv2d(1, 32, 3, 1)
            self.conv2 = nn.Conv2d(32, 64, 3, 1)
            self.dropout1 = nn.Dropout(0.25)
            self.dropout2 = nn.Dropout(0.5)
            self.fc1 = nn.Linear(9216, 128)
            self.fc2 = nn.Linear(128, 10)

        def forward(self, x):
            x = F.relu(self.conv1(x))
            x = F.relu(self.conv2(x))
            x = F.max_pool2d(x, 2)
            x = self.dropout1(x)
            x = torch.flatten(x, 1)
            x = F.relu(self.fc1(x))
            x = self.dropout2(x)
            x = self.fc2(x)
            return F.log_softmax(x, dim=1)

    # Use NCCL for GPU, Gloo for CPU
    device, backend = ("cuda", "nccl") if torch.cuda.is_available() else ("cpu", "gloo")
    print(f"Using Device: {device}, Backend: {backend}")

    # Setup PyTorch distributed
    local_rank = int(os.getenv("LOCAL_RANK", 0))
    dist.init_process_group(backend=backend)
    print(
        f"Distributed Training - WORLD_SIZE: {dist.get_world_size()}, "
        f"RANK: {dist.get_rank()}, LOCAL_RANK: {local_rank}"
    )

    # Create model and move to device
    device = torch.device(f"{device}:{local_rank}")
    model = Net().to(device)
    
    # Use torch.compile for PyTorch 2.0+ optimization (GPU only)
    if torch.cuda.is_available():
        model = torch.compile(model)
    
    model = nn.parallel.DistributedDataParallel(model)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=momentum)

    # Download MNIST only on rank 0
    if local_rank == 0:
        datasets.MNIST(
            "./data",
            train=True,
            download=True,
            transform=transforms.Compose([transforms.ToTensor()]),
        )
    dist.barrier()

    # Load dataset on all workers
    dataset = datasets.MNIST(
        "./data",
        train=True,
        download=False,
        transform=transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ]),
    )

    # Shard dataset across workers
    train_loader = DataLoader(
        dataset,
        batch_size=batch_size,
        sampler=DistributedSampler(dataset)
    )

    dist.barrier()
    
    # Training loop
    for epoch in range(1, num_epochs + 1):
        model.train()

        for batch_idx, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            # Forward pass
            outputs = model(inputs)
            loss = F.nll_loss(outputs, labels)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if batch_idx % 100 == 0 and dist.get_rank() == 0:
                print(
                    f"Epoch {epoch} [{batch_idx * len(inputs)}/{len(train_loader.dataset)} "
                    f"({100.0 * batch_idx / len(train_loader):.0f}%)]\tLoss: {loss.item():.6f}"
                )

    dist.barrier()
    
    if dist.get_rank() == 0:
        print("Training complete!")
        # Save model on rank 0
        torch.save(model.module.state_dict(), "mnist_model.pt")
        print("Model saved to mnist_model.pt")

    dist.destroy_process_group()


if __name__ == "__main__":
    train_mnist()

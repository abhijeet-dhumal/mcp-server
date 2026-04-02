"""Planning tools for resource estimation and cluster inspection.

Maps to cluster inspection functionality:
- get_cluster_resources() → K8s node inspection
- estimate_resources() → Model-based resource estimation
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import ToolError, ToolResponse

MODEL_RESOURCE_ESTIMATES = {
    "llama-3.2-1b": {"gpu": 1, "memory": "16Gi", "gpu_memory": "8GB"},
    "llama-3.2-3b": {"gpu": 1, "memory": "24Gi", "gpu_memory": "16GB"},
    "llama-3.1-8b": {"gpu": 2, "memory": "48Gi", "gpu_memory": "40GB"},
    "llama-3.1-70b": {"gpu": 8, "memory": "256Gi", "gpu_memory": "160GB"},
    "mistral-7b": {"gpu": 1, "memory": "32Gi", "gpu_memory": "24GB"},
    "gemma-2b": {"gpu": 1, "memory": "16Gi", "gpu_memory": "8GB"},
    "gemma-7b": {"gpu": 1, "memory": "32Gi", "gpu_memory": "24GB"},
    "phi-3-mini": {"gpu": 1, "memory": "16Gi", "gpu_memory": "8GB"},
}


def get_cluster_resources() -> dict[str, Any]:
    """Gets available cluster resources (GPUs, nodes).

    Returns GPU availability and node information for capacity planning.
    Call this before submitting training jobs to verify resources.

    Returns:
        JSON with {gpu_total: int, nodes_with_gpu: int, nodes: [{name, gpus, memory}]}

    Note:
        Do NOT use for real-time monitoring. This is a point-in-time snapshot.
    """
    try:
        from kubernetes import client, config

        config.load_config()
        v1 = client.CoreV1Api()

        nodes = v1.list_node()
        gpu_total = 0
        node_info = []

        for node in nodes.items:
            alloc = node.status.allocatable or {}
            gpu = int(alloc.get("nvidia.com/gpu", 0))
            gpu_total += gpu

            node_data = {
                "name": node.metadata.name,
                "memory": alloc.get("memory"),
                "cpu": alloc.get("cpu"),
            }

            if gpu > 0:
                node_data["gpus"] = gpu

            node_info.append(node_data)

        return ToolResponse(
            data={
                "gpu_total": gpu_total,
                "nodes_with_gpu": sum(1 for n in node_info if n.get("gpus", 0) > 0),
                "node_count": len(node_info),
                "nodes": node_info,
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.KUBERNETES_ERROR,
        ).model_dump()


def estimate_resources(
    model: str,
    num_workers: int = 1,
    batch_size: int = 4,
) -> dict[str, Any]:
    """Estimates resource requirements for training a model.

    Returns recommended GPU, memory, and worker configuration based on
    model size and training parameters. Call before fine_tune() to plan.

    Args:
        model: Model name or HuggingFace path (e.g., "meta-llama/Llama-3.2-1B").
        num_workers: Number of parallel training workers (1-8, default 1).
        batch_size: Per-device batch size (1-32, default 4).

    Returns:
        JSON with {gpu_per_worker, memory_per_worker, total_gpu, recommendation}

    Note:
        Estimates are approximations. Actual requirements vary with dataset size.
    """
    try:
        model_key = None
        model_lower = model.lower()
        for key in MODEL_RESOURCE_ESTIMATES:
            if key in model_lower:
                model_key = key
                break

        if model_key:
            base = MODEL_RESOURCE_ESTIMATES[model_key]
            gpu_per_worker = base["gpu"]
            memory = base["memory"]
            gpu_memory = base["gpu_memory"]
        else:
            gpu_per_worker = 1
            memory = "16Gi"
            gpu_memory = "16GB"

        batch_multiplier = max(1, batch_size // 4)
        adjusted_memory = memory.replace("Gi", "")
        adjusted_memory = f"{int(adjusted_memory) * batch_multiplier}Gi"

        total_gpu = gpu_per_worker * num_workers

        return ToolResponse(
            data={
                "model": model,
                "gpu_per_worker": gpu_per_worker,
                "memory_per_worker": adjusted_memory,
                "gpu_memory_per_worker": gpu_memory,
                "total_gpu": total_gpu,
                "num_workers": num_workers,
                "batch_size": batch_size,
                "recommendation": f"Request {total_gpu} GPUs across {num_workers} workers",
                "known_model": model_key is not None,
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()

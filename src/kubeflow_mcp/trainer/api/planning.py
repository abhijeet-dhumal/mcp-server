"""Planning tools for resource estimation and cluster inspection.

These tools don't require TrainerClient - only Kubernetes access.
Ideal for MVP (Stage 2) as they prove the architecture works.
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import ToolError, ToolResponse


def get_cluster_resources() -> dict[str, Any]:
    """Get available cluster resources (GPUs, nodes).

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

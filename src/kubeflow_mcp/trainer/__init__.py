"""TrainerClient integration with MCP tools and skills."""

from kubeflow_mcp.trainer.api.planning import get_cluster_resources

MODULE_INFO = {
    "name": "trainer",
    "description": "Training job management (Kubeflow Training Operator)",
    "sdk_client": "kubeflow.trainer.TrainerClient",
    "status": "implemented",
}

TOOLS = [
    get_cluster_resources,
]

__all__ = ["MODULE_INFO", "TOOLS", "get_cluster_resources"]

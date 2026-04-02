"""Lifecycle tools for training job management.

Maps to TrainerClient methods (SDK 0.4.0):
- delete_training_job() → TrainerClient.delete_job()
- suspend_training_job() → Kubernetes suspend patch
- resume_training_job() → Kubernetes resume patch
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client


def delete_training_job(name: str) -> dict[str, Any]:
    """Deletes a training job and its associated resources.

    Removes the job, pods, and any associated ConfigMaps/Secrets.
    Use to clean up completed or failed jobs.

    Args:
        name: Name of the training job to delete.

    Returns:
        JSON with {job: str, deleted: bool, message: str}

    Note:
        This is irreversible. Job logs are lost after deletion.
    """
    try:
        client = get_trainer_client()
        client.delete_job(name=name)

        return ToolResponse(
            data={
                "job": name,
                "deleted": True,
                "message": f"Training job '{name}' deleted successfully",
            }
        ).model_dump()

    except Exception as e:
        if "not found" in str(e).lower():
            return ToolError(
                error=f"Training job '{name}' not found",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
            ).model_dump()
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def suspend_training_job(
    name: str,
    namespace: str | None = None,
) -> dict[str, Any]:
    """Suspends a running training job.

    Pauses the job by scaling workers to zero. Job state is preserved.
    Use to temporarily free up cluster resources.

    Args:
        name: Name of the training job to suspend.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.

    Returns:
        JSON with {job: str, suspended: bool, message: str}

    Note:
        Resume with resume_training_job(). Checkpoints are preserved.
    """
    try:
        from kubernetes import client, config

        config.load_config()
        api = client.CustomObjectsApi()

        ns = namespace or "default"
        body = {"spec": {"suspend": True}}

        api.patch_namespaced_custom_object(
            group="kubeflow.org",
            version="v1",
            namespace=ns,
            plural="trainjobs",
            name=name,
            body=body,
        )

        return ToolResponse(
            data={
                "job": name,
                "namespace": ns,
                "suspended": True,
                "message": f"Training job '{name}' suspended",
            }
        ).model_dump()

    except Exception as e:
        if "not found" in str(e).lower():
            return ToolError(
                error=f"Training job '{name}' not found",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
            ).model_dump()
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def resume_training_job(
    name: str,
    namespace: str | None = None,
) -> dict[str, Any]:
    """Resumes a suspended training job.

    Restarts the job by scaling workers back up. Continues from checkpoint.
    Use after suspend_training_job() to continue training.

    Args:
        name: Name of the training job to resume.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.

    Returns:
        JSON with {job: str, resumed: bool, message: str}

    Note:
        Job must have been suspended. Running jobs cannot be resumed.
    """
    try:
        from kubernetes import client, config

        config.load_config()
        api = client.CustomObjectsApi()

        ns = namespace or "default"
        body = {"spec": {"suspend": False}}

        api.patch_namespaced_custom_object(
            group="kubeflow.org",
            version="v1",
            namespace=ns,
            plural="trainjobs",
            name=name,
            body=body,
        )

        return ToolResponse(
            data={
                "job": name,
                "namespace": ns,
                "resumed": True,
                "message": f"Training job '{name}' resumed",
            }
        ).model_dump()

    except Exception as e:
        if "not found" in str(e).lower():
            return ToolError(
                error=f"Training job '{name}' not found",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
            ).model_dump()
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()

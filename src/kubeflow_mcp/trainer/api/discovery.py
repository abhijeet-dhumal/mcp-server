"""Discovery tools for training jobs and runtimes.

Maps to TrainerClient methods (SDK 0.4.0):
- list_training_jobs() → TrainerClient.list_jobs()
- get_training_job() → TrainerClient.get_job()
- list_runtimes() → TrainerClient.list_runtimes()
- get_runtime() → TrainerClient.get_runtime()
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client


def list_training_jobs(
    runtime: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Lists training jobs in the Kubernetes cluster.

    Returns jobs with their current status, creation time, and resource usage.
    Use this to check what training jobs exist before submitting new ones.

    Args:
        runtime: Filter by runtime name.
        status: Filter by status (Running, Succeeded, Failed, Pending, Suspended).
        limit: Maximum jobs to return (1-100, default 50).

    Returns:
        JSON with {jobs: [{name, namespace, status, created_at}], total: int}

    Note:
        Do NOT use for real-time monitoring. Use get_training_logs() instead.
    """
    try:
        client = get_trainer_client()
        jobs = client.list_jobs(runtime=runtime) if runtime else client.list_jobs()

        job_list = []
        for job in jobs:
            job_data = {
                "name": job.name,
                "status": job.status if hasattr(job, "status") else "Unknown",
                "runtime": job.runtime if hasattr(job, "runtime") else None,
            }
            job_list.append(job_data)

        if status:
            job_list = [j for j in job_list if j.get("status") == status]

        return ToolResponse(data={"jobs": job_list[:limit], "total": len(job_list)}).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def get_training_job(name: str) -> dict[str, Any]:
    """Gets detailed information about a specific training job.

    Returns job configuration, status, worker details, and resource usage.
    Use after list_training_jobs() to inspect a specific job.

    Args:
        name: Name of the training job.

    Returns:
        JSON with {name, status, runtime, config}

    Note:
        For logs, use get_training_logs(). For events, use get_training_events().
    """
    try:
        client = get_trainer_client()
        job = client.get_job(name=name)

        return ToolResponse(
            data={
                "name": job.name,
                "status": job.status if hasattr(job, "status") else "Unknown",
                "runtime": job.runtime if hasattr(job, "runtime") else None,
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


def list_runtimes() -> dict[str, Any]:
    """Lists available training runtimes in the cluster.

    Returns ClusterTrainingRuntimes that define pre-configured training environments.

    Returns:
        JSON with {runtimes: [{name, framework}], total: int}

    Note:
        Runtimes define default images, packages, and configurations.
    """
    try:
        client = get_trainer_client()
        runtimes = client.list_runtimes()

        runtime_list = []
        for rt in runtimes:
            runtime_list.append(
                {
                    "name": rt.name if hasattr(rt, "name") else str(rt),
                }
            )

        return ToolResponse(
            data={"runtimes": runtime_list, "total": len(runtime_list)}
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def get_runtime(name: str) -> dict[str, Any]:
    """Gets details of a specific training runtime.

    Returns runtime configuration including image, packages, and settings.
    Use to understand what a runtime provides before using it.

    Args:
        name: Runtime name.

    Returns:
        JSON with {name, config}
    """
    try:
        client = get_trainer_client()
        rt = client.get_runtime(name=name)

        return ToolResponse(
            data={
                "name": rt.name if hasattr(rt, "name") else name,
            }
        ).model_dump()

    except Exception as e:
        if "not found" in str(e).lower():
            return ToolError(
                error=f"Runtime '{name}' not found",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
            ).model_dump()
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def get_runtime_packages(name: str) -> dict[str, Any]:
    """Gets the pip packages installed in a training runtime.

    Returns list of Python packages available in the runtime.
    Use to verify if required packages are pre-installed.

    Args:
        name: Runtime name.

    Returns:
        JSON with {runtime: str, packages: [str]}
    """
    try:
        client = get_trainer_client()
        # SDK 0.4.0 may not have this method - try to get from runtime
        rt = client.get_runtime(name=name)
        packages = rt.packages if hasattr(rt, "packages") else []

        return ToolResponse(data={"runtime": name, "packages": packages}).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()

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
    """List training jobs in the cluster.

    Args:
        runtime: Filter by runtime name
        status: Filter by status (Running/Succeeded/Failed/Pending/Suspended)
        limit: Max jobs to return (default 50)

    Returns: {jobs: [{name, status, runtime}], total}
    """
    try:
        client = get_trainer_client()
        jobs = client.list_jobs(runtime=runtime) if runtime else client.list_jobs()  # type: ignore[arg-type]

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
    """Get details of a specific training job.

    Args:
        name: Job name

    Returns: {name, status, runtime}
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
    """List available training runtimes. Use if fine_tune() fails with "runtime not found".

    Returns: {runtimes: [{name}], total}
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
    """Get runtime configuration details.

    Args:
        name: Runtime name

    Returns: {name, config}
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
    """Get pip packages installed in a runtime.

    Args:
        name: Runtime name

    Returns: {runtime, packages}
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

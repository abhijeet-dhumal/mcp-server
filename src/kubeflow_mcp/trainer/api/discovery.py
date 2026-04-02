"""Discovery tools for training jobs and runtimes.

Maps to TrainerClient methods:
- list_training_jobs() → TrainerClient.list_jobs()
- get_training_job() → TrainerClient.get_job()
- list_runtimes() → TrainerClient.list_runtimes()
- get_runtime() → TrainerClient.get_runtime()
- get_runtime_packages() → TrainerClient.get_runtime_packages()
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client


def list_training_jobs(
    namespace: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Lists training jobs in the Kubernetes cluster.

    Returns jobs with their current status, creation time, and resource usage.
    Use this to check what training jobs exist before submitting new ones.

    Args:
        namespace: Filter by namespace. Defaults to current kubeconfig context.
        status: Filter by status (Running, Succeeded, Failed, Pending, Suspended).
        limit: Maximum jobs to return (1-100, default 50).

    Returns:
        JSON with {jobs: [{name, namespace, status, created_at}], total: int}

    Note:
        Do NOT use for real-time monitoring. Use get_training_logs() instead.
    """
    try:
        client = get_trainer_client()
        jobs = client.list_jobs(namespace=namespace)

        job_list = []
        for job in jobs:
            job_data = {
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "status": _get_job_status(job),
                "created_at": (
                    job.metadata.creation_timestamp.isoformat()
                    if job.metadata.creation_timestamp
                    else None
                ),
            }
            job_list.append(job_data)

        if status:
            job_list = [j for j in job_list if j["status"] == status]

        return ToolResponse(data={"jobs": job_list[:limit], "total": len(job_list)}).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def get_training_job(
    name: str,
    namespace: str | None = None,
) -> dict[str, Any]:
    """Gets detailed information about a specific training job.

    Returns job configuration, status, worker details, and resource usage.
    Use after list_training_jobs() to inspect a specific job.

    Args:
        name: Name of the training job.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.

    Returns:
        JSON with {name, status, workers, resources, config, created_at}

    Note:
        For logs, use get_training_logs(). For events, use get_training_events().
    """
    try:
        client = get_trainer_client()
        job = client.get_job(name=name, namespace=namespace)

        return ToolResponse(
            data={
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "status": _get_job_status(job),
                "created_at": (
                    job.metadata.creation_timestamp.isoformat()
                    if job.metadata.creation_timestamp
                    else None
                ),
                "workers": _get_worker_count(job),
                "spec": _extract_job_spec(job),
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


def list_runtimes(
    namespace: str | None = None,
) -> dict[str, Any]:
    """Lists available training runtimes in the cluster.

    Returns ClusterTrainingRuntimes (cluster-scoped) and TrainingRuntimes
    (namespace-scoped) that define pre-configured training environments.

    Args:
        namespace: Filter by namespace for namespace-scoped runtimes.

    Returns:
        JSON with {runtimes: [{name, scope, framework, image}], total: int}

    Note:
        Runtimes define default images, packages, and configurations.
    """
    try:
        client = get_trainer_client()
        runtimes = client.list_runtimes(namespace=namespace)

        runtime_list = []
        for rt in runtimes:
            runtime_list.append(
                {
                    "name": rt.metadata.name,
                    "scope": "cluster" if not hasattr(rt.metadata, "namespace") else "namespace",
                    "namespace": getattr(rt.metadata, "namespace", None),
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


def get_runtime(
    name: str,
    namespace: str | None = None,
) -> dict[str, Any]:
    """Gets details of a specific training runtime.

    Returns runtime configuration including image, packages, and settings.
    Use to understand what a runtime provides before using it.

    Args:
        name: Runtime name.
        namespace: Namespace for namespace-scoped runtimes.

    Returns:
        JSON with {name, scope, image, packages, config}
    """
    try:
        client = get_trainer_client()
        rt = client.get_runtime(name=name, namespace=namespace)

        return ToolResponse(
            data={
                "name": rt.metadata.name,
                "namespace": getattr(rt.metadata, "namespace", None),
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


def get_runtime_packages(
    name: str,
    namespace: str | None = None,
) -> dict[str, Any]:
    """Gets the pip packages installed in a training runtime.

    Returns list of Python packages available in the runtime.
    Use to verify if required packages are pre-installed.

    Args:
        name: Runtime name.
        namespace: Namespace for namespace-scoped runtimes.

    Returns:
        JSON with {runtime: str, packages: [str]}
    """
    try:
        client = get_trainer_client()
        packages = client.get_runtime_packages(name=name, namespace=namespace)

        return ToolResponse(data={"runtime": name, "packages": packages}).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def _get_job_status(job: Any) -> str:
    """Extract job status from conditions."""
    if not job.status or not job.status.conditions:
        return "Pending"

    for cond in reversed(job.status.conditions):
        if cond.status == "True":
            return cond.type
    return "Unknown"


def _get_worker_count(job: Any) -> dict[str, int]:
    """Extract worker counts from job spec."""
    if not job.spec or not job.spec.trainer_replica_specs:
        return {"total": 0}

    workers = {}
    total = 0
    for name, spec in job.spec.trainer_replica_specs.items():
        count = spec.replicas or 0
        workers[name.lower()] = count
        total += count
    workers["total"] = total
    return workers


def _extract_job_spec(job: Any) -> dict[str, Any]:
    """Extract relevant job spec details."""
    spec = {}
    if job.spec:
        if hasattr(job.spec, "runtime_ref") and job.spec.runtime_ref:
            spec["runtime"] = job.spec.runtime_ref.name
    return spec

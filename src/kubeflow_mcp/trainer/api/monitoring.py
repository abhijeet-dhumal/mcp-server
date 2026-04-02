"""Monitoring tools for training job logs and events.

Maps to TrainerClient methods:
- get_training_logs() → TrainerClient.get_job_logs()
- get_training_events() → TrainerClient.get_job_events()
- wait_for_training() → TrainerClient.wait_for_job_status()
"""

import time
from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client
from kubeflow_mcp.core.security import sanitize_log_output


def get_training_logs(
    name: str,
    namespace: str | None = None,
    worker: str = "worker-0",
    tail_lines: int = 100,
    follow: bool = False,
) -> dict[str, Any]:
    """Gets logs from a training job worker.

    Returns recent log output from a specific worker pod.
    Use for debugging training issues or monitoring progress.

    Args:
        name: Name of the training job.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.
        worker: Worker pod to get logs from (default "worker-0").
        tail_lines: Number of lines from end (1-1000, default 100).
        follow: Stream logs continuously (default False).

    Returns:
        JSON with {job: str, worker: str, logs: str, lines: int}

    Note:
        For job status, use get_training_job(). This is for raw logs only.
    """
    try:
        client = get_trainer_client()
        logs = client.get_job_logs(
            name=name,
            namespace=namespace,
            # replica_index=int(worker.split("-")[-1]) if "-" in worker else 0,
            tail_lines=tail_lines,
            follow=follow,
        )

        sanitized = sanitize_log_output(logs)

        return ToolResponse(
            data={
                "job": name,
                "worker": worker,
                "logs": sanitized,
                "lines": len(sanitized.split("\n")),
            }
        ).model_dump()

    except Exception as e:
        if "not found" in str(e).lower():
            return ToolError(
                error=f"Training job '{name}' or worker '{worker}' not found",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
            ).model_dump()
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def get_training_events(
    name: str,
    namespace: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Gets Kubernetes events for a training job.

    Returns events like pod scheduling, image pulls, and failures.
    Use to understand why a job is pending or failed.

    Args:
        name: Name of the training job.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.
        limit: Maximum events to return (1-100, default 50).

    Returns:
        JSON with {job: str, events: [{type, reason, message, timestamp}]}

    Note:
        Events are ephemeral. Old events may be garbage collected.
    """
    try:
        client = get_trainer_client()
        events = client.get_job_events(name=name, namespace=namespace)

        event_list = []
        for event in events[:limit]:
            event_list.append(
                {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "timestamp": (
                        event.last_timestamp.isoformat() if event.last_timestamp else None
                    ),
                }
            )

        return ToolResponse(
            data={"job": name, "events": event_list, "total": len(events)}
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def wait_for_training(
    name: str,
    namespace: str | None = None,
    target_status: str = "Succeeded",
    timeout_seconds: int = 600,
    poll_interval: int = 10,
) -> dict[str, Any]:
    """Waits for a training job to reach a target status.

    Polls job status until target is reached or timeout occurs.
    Use after submitting a job to wait for completion.

    Args:
        name: Name of the training job.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.
        target_status: Status to wait for (Succeeded, Failed, Running).
        timeout_seconds: Maximum wait time (60-3600, default 600).
        poll_interval: Seconds between status checks (5-60, default 10).

    Returns:
        JSON with {job: str, status: str, reached: bool, elapsed_seconds: int}

    Note:
        This blocks until status is reached. Use get_training_job() for async checks.
    """
    try:
        client = get_trainer_client()
        start_time = time.time()
        terminal_statuses = {"Succeeded", "Failed"}

        while True:
            elapsed = int(time.time() - start_time)
            if elapsed > timeout_seconds:
                return ToolResponse(
                    data={
                        "job": name,
                        "status": "Unknown",
                        "reached": False,
                        "elapsed_seconds": elapsed,
                        "message": f"Timeout after {timeout_seconds}s",
                    }
                ).model_dump()

            try:
                job = client.get_job(name=name, namespace=namespace)
                current_status = _get_job_status(job)

                if current_status == target_status:
                    return ToolResponse(
                        data={
                            "job": name,
                            "status": current_status,
                            "reached": True,
                            "elapsed_seconds": elapsed,
                            "message": f"Job reached {target_status}",
                        }
                    ).model_dump()

                if current_status in terminal_statuses and target_status not in terminal_statuses:
                    return ToolResponse(
                        data={
                            "job": name,
                            "status": current_status,
                            "reached": False,
                            "elapsed_seconds": elapsed,
                            "message": f"Job ended with {current_status}, not {target_status}",
                        }
                    ).model_dump()

            except Exception:
                pass

            time.sleep(poll_interval)

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

"""Monitoring tools for training job logs and events.

Maps to TrainerClient methods (SDK 0.4.0):
- get_training_logs() → TrainerClient.get_job_logs()
- get_training_events() → TrainerClient.get_job_events()
- wait_for_training() → TrainerClient.wait_for_job_status()
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client
from kubeflow_mcp.core.security import sanitize_log_output


def get_training_logs(
    name: str,
    step: str = "node-0",
    follow: bool = False,
) -> dict[str, Any]:
    """Get logs from a training job. Use for debugging.

    Args:
        name: Job name
        step: Node to get logs from (default "node-0")
        follow: Stream continuously (default False)

    Returns: {job, step, logs, lines}
    """
    try:
        client = get_trainer_client()
        logs_iter = client.get_job_logs(name=name, step=step, follow=follow)

        # Collect logs (non-follow mode)
        logs = "\n".join(logs_iter) if not follow else "Streaming not supported in this context"
        sanitized = sanitize_log_output(logs)

        return ToolResponse(
            data={
                "job": name,
                "step": step,
                "logs": sanitized,
                "lines": len(sanitized.split("\n")),
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


def get_training_events(
    name: str,
    limit: int = 50,
) -> dict[str, Any]:
    """Get K8s events for a job. Use to debug pending/failed jobs.

    Args:
        name: Job name
        limit: Max events (default 50)

    Returns: {job, events: [{type, reason, message}]}
    """
    try:
        client = get_trainer_client()
        events = client.get_job_events(name=name)

        event_list = []
        for event in events[:limit]:
            event_list.append(
                {
                    "type": event.type if hasattr(event, "type") else "Unknown",
                    "reason": event.reason if hasattr(event, "reason") else "",
                    "message": event.message if hasattr(event, "message") else "",
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
    target_status: str = "Complete",
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    """Wait for job to reach target status. Blocks until done.

    Args:
        name: Job name
        target_status: Status to wait for (Complete/Failed)
        timeout_seconds: Max wait time (default 600)

    Returns: {job, status, reached}
    """
    try:
        client = get_trainer_client()

        job = client.wait_for_job_status(
            name=name,
            status={target_status},
            timeout=timeout_seconds,
        )

        return ToolResponse(
            data={
                "job": name,
                "status": job.status if hasattr(job, "status") else "Unknown",
                "reached": True,
                "message": f"Job reached {target_status}",
            }
        ).model_dump()

    except TimeoutError:
        return ToolResponse(
            data={
                "job": name,
                "status": "Unknown",
                "reached": False,
                "message": f"Timeout after {timeout_seconds}s",
            }
        ).model_dump()
    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()

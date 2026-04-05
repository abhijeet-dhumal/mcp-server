# Copyright 2024 The Kubeflow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    """Get pod logs from a training job.

    Args:
        name: TrainJob name.
        step: Node/worker to get logs from. Defaults to ``node-0``.
        follow: Stream logs continuously (not supported in MCP context).

    Returns:
        dict: Response containing:

        - ``job`` (str): Job name
        - ``step`` (str): Node name
        - ``logs`` (str): Sanitized log output
        - ``lines`` (int): Number of log lines

    Raises:
        ToolError: If job not found (``RESOURCE_NOT_FOUND``).
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
                hint="Use list_training_jobs to find available jobs",
            ).model_dump()
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
            hint="Use monitoring_workflow prompt for debugging guidance",
        ).model_dump()


def get_training_events(
    name: str,
    limit: int = 50,
) -> dict[str, Any]:
    """Get Kubernetes events for a training job.

    Useful for debugging pending jobs (scheduling issues) or failures.

    Args:
        name: TrainJob name.
        limit: Maximum events to return. Defaults to 50.

    Returns:
        dict: Response containing:

        - ``job`` (str): Job name
        - ``events`` (list): Events with ``type``, ``reason``, ``message``
        - ``total`` (int): Total event count
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
            hint="Use monitoring_workflow prompt for debugging guidance",
        ).model_dump()


def wait_for_training(
    name: str,
    target_status: str = "Complete",
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    """Wait for a job to reach a target status.

    Blocks until the job completes, fails, or times out.

    Args:
        name: TrainJob name.
        target_status: Status to wait for (``Complete`` or ``Failed``). Defaults to ``Complete``.
        timeout_seconds: Maximum wait time in seconds. Defaults to 600 (10 min).

    Returns:
        dict: Response containing:

        - ``job`` (str): Job name
        - ``status`` (str): Final job status
        - ``reached`` (bool): Whether target status was reached
        - ``message`` (str): Status message or timeout notice
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
                "hint": "Use get_training_events to check for scheduling issues",
            }
        ).model_dump()
    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
            hint="Use monitoring_workflow prompt for debugging guidance",
        ).model_dump()

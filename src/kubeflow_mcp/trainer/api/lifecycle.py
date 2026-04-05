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
    """Delete a training job permanently.

    This operation is irreversible - all job resources are removed.

    Args:
        name: TrainJob name to delete.

    Returns:
        dict: Response containing ``job``, ``deleted`` (bool), ``message``.

    Raises:
        ToolError: If job not found (``RESOURCE_NOT_FOUND``).

    Warning:
        Requires confirmation in MCP clients - accidental deletion prevented.
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
    """Pause a running training job.

    Suspends job execution without deleting. Resume with ``resume_training_job()``.

    Args:
        name: TrainJob name.
        namespace: K8s namespace. Defaults to kubeconfig context.

    Returns:
        dict: Response containing ``job``, ``namespace``, ``suspended`` (bool), ``message``.

    Raises:
        ToolError: If job not found (``RESOURCE_NOT_FOUND``).
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
    """Resume a suspended training job.

    Args:
        name: TrainJob name.
        namespace: K8s namespace. Defaults to kubeconfig context.

    Returns:
        dict: Response containing ``job``, ``namespace``, ``resumed`` (bool), ``message``.

    Raises:
        ToolError: If job not found (``RESOURCE_NOT_FOUND``).
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

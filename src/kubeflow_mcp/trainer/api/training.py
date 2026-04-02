"""Training tools for LLM fine-tuning and custom training.

Maps to TrainerClient.train() with different configurations:
- fine_tune() → HuggingFace model fine-tuning
- run_custom_training() → User-provided training script
- run_container_training() → Pre-built container image
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import PreviewResponse, ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client
from kubeflow_mcp.core.security import is_safe_python_code, validate_k8s_name


def fine_tune(
    model: str,
    dataset: str,
    name: str | None = None,
    namespace: str | None = None,
    num_workers: int = 1,
    gpu_per_worker: int = 1,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-5,
    lora: bool = True,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Submits a fine-tuning job for a HuggingFace model.

    Creates a distributed training job using LoRA (default) or full fine-tuning.
    Use estimate_resources() first to determine appropriate resource settings.

    Args:
        model: HuggingFace model path (e.g., "meta-llama/Llama-3.2-1B").
        dataset: HuggingFace dataset path (e.g., "imdatta0/ultrachat_1k").
        name: Job name. Auto-generated if not provided.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.
        num_workers: Number of training workers (1-8, default 1).
        gpu_per_worker: GPUs per worker (1-8, default 1).
        epochs: Training epochs (1-100, default 3).
        batch_size: Per-device batch size (1-32, default 4).
        learning_rate: Learning rate (default 2e-5).
        lora: Use LoRA for efficient fine-tuning (default True).
        confirmed: Set True to execute. Returns preview if False.

    Returns:
        Preview: config summary if confirmed=False
        Success: {job_name, namespace, status, message}

    Note:
        Requires HF_TOKEN environment variable for gated models (Llama, etc).
    """
    try:
        if name:
            err = validate_k8s_name(name)
            if err:
                return err.model_dump()

        config = {
            "model": model,
            "dataset": dataset,
            "name": name,
            "namespace": namespace,
            "num_workers": num_workers,
            "resources_per_worker": {"gpu": gpu_per_worker},
            "trainer_config": {
                "num_epochs": epochs,
                "per_device_train_batch_size": batch_size,
                "learning_rate": learning_rate,
            },
            "lora_config": {"r": 8, "lora_alpha": 16} if lora else None,
        }

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        client = get_trainer_client()
        job_name = client.train(
            model=model,
            dataset=dataset,
            name=name,
            namespace=namespace,
            num_workers=num_workers,
            resources_per_worker={"gpu": gpu_per_worker},
            trainer_config={
                "num_epochs": epochs,
                "per_device_train_batch_size": batch_size,
                "learning_rate": learning_rate,
            },
            lora_config={"r": 8, "lora_alpha": 16} if lora else None,
        )

        return ToolResponse(
            data={
                "job_name": job_name,
                "namespace": namespace or "default",
                "status": "Created",
                "message": f"Training job '{job_name}' submitted successfully",
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def run_custom_training(
    script: str,
    name: str | None = None,
    namespace: str | None = None,
    num_workers: int = 1,
    gpu_per_worker: int = 1,
    packages: list[str] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Submits a training job with custom Python script.

    Executes user-provided training code in a distributed environment.
    Script is validated for security before execution.

    Args:
        script: Python training script content (validated for safety).
        name: Job name. Auto-generated if not provided.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.
        num_workers: Number of training workers (1-8, default 1).
        gpu_per_worker: GPUs per worker (1-8, default 1).
        packages: Additional pip packages to install (e.g., ["transformers"]).
        confirmed: Set True to execute. Returns preview if False.

    Returns:
        Preview: config summary if confirmed=False
        Success: {job_name, namespace, status, message}

    Note:
        Script cannot import os, subprocess, or use eval/exec.
    """
    try:
        safe, reason = is_safe_python_code(script)
        if not safe:
            return ToolError(
                error=f"Script validation failed: {reason}",
                error_code=ErrorCode.VALIDATION_ERROR,
            ).model_dump()

        if name:
            err = validate_k8s_name(name)
            if err:
                return err.model_dump()

        config = {
            "script": script[:200] + "..." if len(script) > 200 else script,
            "name": name,
            "namespace": namespace,
            "num_workers": num_workers,
            "resources_per_worker": {"gpu": gpu_per_worker},
            "packages": packages or [],
        }

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        client = get_trainer_client()
        job_name = client.train(
            func=lambda: exec(script),  # noqa: S102
            name=name,
            namespace=namespace,
            num_workers=num_workers,
            resources_per_worker={"gpu": gpu_per_worker},
            packages_to_install=packages,
        )

        return ToolResponse(
            data={
                "job_name": job_name,
                "namespace": namespace or "default",
                "status": "Created",
                "message": f"Custom training job '{job_name}' submitted",
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def run_container_training(
    image: str,
    name: str | None = None,
    namespace: str | None = None,
    num_workers: int = 1,
    gpu_per_worker: int = 1,
    command: list[str] | None = None,
    env: dict[str, str] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Submits a training job using a pre-built container image.

    Runs distributed training with a custom Docker/OCI image.
    Use when you have a pre-packaged training environment.

    Args:
        image: Container image (e.g., "pytorch/pytorch:2.0-cuda11.8").
        name: Job name. Auto-generated if not provided.
        namespace: Kubernetes namespace. Uses kubeconfig default if not set.
        num_workers: Number of training workers (1-8, default 1).
        gpu_per_worker: GPUs per worker (1-8, default 1).
        command: Override container command (e.g., ["python", "train.py"]).
        env: Environment variables as key-value pairs.
        confirmed: Set True to execute. Returns preview if False.

    Returns:
        Preview: config summary if confirmed=False
        Success: {job_name, namespace, status, message}

    Note:
        Image must be accessible from the cluster (public or with imagePullSecrets).
    """
    try:
        if name:
            err = validate_k8s_name(name)
            if err:
                return err.model_dump()

        config = {
            "image": image,
            "name": name,
            "namespace": namespace,
            "num_workers": num_workers,
            "resources_per_worker": {"gpu": gpu_per_worker},
            "command": command,
            "env": env,
        }

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        client = get_trainer_client()
        job_name = client.train(
            image=image,
            name=name,
            namespace=namespace,
            num_workers=num_workers,
            resources_per_worker={"gpu": gpu_per_worker},
            command=command,
            env=env,
        )

        return ToolResponse(
            data={
                "job_name": job_name,
                "namespace": namespace or "default",
                "status": "Created",
                "message": f"Container training job '{job_name}' submitted",
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()

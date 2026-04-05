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

"""Training tools for LLM fine-tuning and custom training.

Maps to TrainerClient.train() (SDK 0.4.0) with different configurations:
- fine_tune() → HuggingFace model fine-tuning with BuiltinTrainer
- run_custom_training() → User-provided training script with CustomTrainer
- run_container_training() → Pre-built container image with CustomTrainerContainer
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import PreviewResponse, ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client
from kubeflow_mcp.core.security import is_safe_python_code, validate_k8s_name

# Import Kubeflow SDK types at module level to avoid import deadlocks
# when tools are called in rapid succession
try:
    from kubeflow.trainer.options import (  # type: ignore[attr-defined]
        ContainerPatch,
        JobSetSpecPatch,
        JobSetTemplatePatch,
        JobSpecPatch,
        JobTemplatePatch,
        PodSpecPatch,
        PodTemplatePatch,
        ReplicatedJobPatch,
        RuntimePatch,
        TrainingRuntimeSpecPatch,
    )
    from kubeflow.trainer.types.types import (
        BuiltinTrainer,
        CustomTrainer,
        CustomTrainerContainer,
        HuggingFaceDatasetInitializer,
        HuggingFaceModelInitializer,
        Initializer,
        LoraConfig,
        TorchTuneConfig,
    )

    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


def _build_runtime_patch(
    node_selector: dict[str, str] | None = None,
    tolerations: list[dict[str, Any]] | None = None,
    env: list[dict[str, Any]] | None = None,
    volumes: list[dict[str, Any]] | None = None,
    volume_mounts: list[dict[str, Any]] | None = None,
) -> list[Any]:
    """Build RuntimePatch options for the SDK.

    Returns a list of options to pass to client.train(options=...).
    Returns empty list if no patches specified.
    """
    if not any([node_selector, tolerations, env, volumes, volume_mounts]):
        return []

    if not _SDK_AVAILABLE:
        return []

    # Build container patches (env, volume_mounts)
    containers = None
    if env or volume_mounts:
        containers = [
            ContainerPatch(
                name="trainer",  # Default trainer container name
                env=env,
                volume_mounts=volume_mounts,
            )
        ]

    # Build pod spec patch
    pod_spec = PodSpecPatch(
        node_selector=node_selector,
        tolerations=tolerations,
        volumes=volumes,
        containers=containers,
    )

    # Build the full patch hierarchy
    patch = RuntimePatch(
        training_runtime_spec=TrainingRuntimeSpecPatch(
            template=JobSetTemplatePatch(
                spec=JobSetSpecPatch(
                    replicated_jobs=[
                        ReplicatedJobPatch(
                            name="node",  # Default replicated job name
                            template=JobTemplatePatch(
                                spec=JobSpecPatch(
                                    template=PodTemplatePatch(
                                        spec=pod_spec,
                                    ),
                                ),
                            ),
                        ),
                    ],
                ),
            ),
        ),
    )

    return [patch]


def fine_tune(
    model: str,
    dataset: str,
    runtime: str = "torch-tune",
    hf_token: str | None = None,
    # Training parameters (TorchTuneConfig)
    batch_size: int = 4,
    epochs: int = 1,
    num_nodes: int = 1,
    lora_rank: int = 8,
    lora_alpha: int = 16,
    # Runtime patches
    node_selector: dict[str, str] | None = None,
    tolerations: list[dict[str, Any]] | None = None,
    env: list[dict[str, Any]] | None = None,
    volumes: list[dict[str, Any]] | None = None,
    volume_mounts: list[dict[str, Any]] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Fine-tune a HuggingFace model using LoRA/QLoRA with torchtune.

    Requires ``confirmed=True`` to submit. First call returns a preview.

    Args:
        model: HuggingFace model with ``hf://`` prefix (e.g., ``hf://google/gemma-2b``).
        dataset: HuggingFace dataset with ``hf://`` prefix (e.g., ``hf://tatsu-lab/alpaca``).
        runtime: ClusterTrainingRuntime name. Defaults to ``torch-tune``.
        hf_token: Access token for gated models (Llama, Mistral).
        batch_size: Per-GPU batch size. Defaults to 4.
        epochs: Number of training epochs. Defaults to 1.
        num_nodes: Distributed training nodes. Defaults to 1.
        lora_rank: LoRA rank for PEFT. Defaults to 8.
        lora_alpha: LoRA alpha scaling. Defaults to 16.
        node_selector: K8s node selector (e.g., ``{"gpu-type": "a100"}``).
        tolerations: K8s tolerations for tainted nodes.
        env: Additional environment variables.
        volumes: K8s volume definitions.
        volume_mounts: K8s volume mounts.
        confirmed: Set ``True`` to submit job. ``False`` returns preview only.

    Returns:
        dict: If ``confirmed=False``: preview with ``config`` dict.
            If ``confirmed=True``: ``job_name``, ``status``, ``message``.

    Example:
        >>> fine_tune("hf://google/gemma-2b", "hf://tatsu-lab/alpaca", confirmed=True)
        {"data": {"job_name": "train-gemma-abc", "status": "Created"}}

    Note:
        Call ``get_cluster_resources()`` first to verify GPU availability.
    """
    try:
        if not _SDK_AVAILABLE:
            return ToolError(
                error="Kubeflow SDK not available",
                error_code=ErrorCode.SDK_ERROR,
            ).model_dump()

        config: dict[str, Any] = {
            "model": model,
            "dataset": dataset,
            "runtime": runtime,
            "hf_token": "***" if hf_token else None,
            # Training params
            "batch_size": batch_size,
            "epochs": epochs,
            "num_nodes": num_nodes,
            "lora_rank": lora_rank,
            "lora_alpha": lora_alpha,
        }

        # Add runtime patches to preview if specified
        if node_selector:
            config["node_selector"] = node_selector
        if tolerations:
            config["tolerations"] = tolerations
        if env:
            config["env"] = env
        if volumes:
            config["volumes"] = volumes
        if volume_mounts:
            config["volume_mounts"] = volume_mounts

        # Check if runtime supports HuggingFace initializers
        # Runtimes like 'torch-tune' have model-initializer and dataset-initializer jobs
        # Runtimes like 'torch-distributed' do NOT - use CustomTrainer approach instead
        hf_compatible_runtimes = ["torch-tune", "torchtune"]
        use_initializer_pattern = runtime in hf_compatible_runtimes

        if use_initializer_pattern:
            config["mode"] = "builtin_trainer"
            config["note"] = "Using BuiltinTrainer with TorchTuneConfig + Initializers"
        else:
            config["mode"] = "custom_trainer"
            config["note"] = (
                f"Runtime '{runtime}' doesn't have initializer jobs. "
                "Using CustomTrainer with packages_to_install instead."
            )

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        # Build runtime patch options if any patches specified
        options = _build_runtime_patch(
            node_selector=node_selector,
            tolerations=tolerations,
            env=env,
            volumes=volumes,
            volume_mounts=volume_mounts,
        )

        client = get_trainer_client()

        if use_initializer_pattern:
            # Use BuiltinTrainer + Initializer pattern
            # (runtime has model-initializer/dataset-initializer jobs)
            initializer = Initializer(
                model=HuggingFaceModelInitializer(
                    storage_uri=model,
                    access_token=hf_token,
                ),
                dataset=HuggingFaceDatasetInitializer(
                    storage_uri=dataset,
                    access_token=hf_token,
                ),
            )

            # Configure BuiltinTrainer with TorchTuneConfig
            trainer = BuiltinTrainer(
                config=TorchTuneConfig(
                    batch_size=batch_size,
                    epochs=epochs,
                    num_nodes=num_nodes,
                    peft_config=LoraConfig(
                        lora_rank=lora_rank,
                        lora_alpha=lora_alpha,
                    ),
                )
            )

            job_name = client.train(
                runtime=runtime,
                initializer=initializer,
                trainer=trainer,
                options=options if options else None,
            )
        else:
            # Use CustomTrainer pattern (runtime doesn't have initializer jobs)
            # Downloads model/dataset inside the training function
            model_id = model.removeprefix("hf://")
            dataset_id = dataset.removeprefix("hf://")

            # Generate training script that downloads and fine-tunes using torchtune
            training_script = f'''
import os
from huggingface_hub import snapshot_download, login
from datasets import load_dataset

# Login if token provided
hf_token = os.environ.get("HF_TOKEN")
if hf_token:
    login(token=hf_token)

# Download model and dataset
print("Downloading model: {model_id}")
snapshot_download("{model_id}", local_dir="/workspace/model")

print("Downloading dataset: {dataset_id}")
ds = load_dataset("{dataset_id}")
ds.save_to_disk("/workspace/dataset")

# Run torchtune LoRA fine-tuning
print("Starting fine-tuning with torchtune...")
print("Config: batch_size={batch_size}, epochs={epochs}, lora_rank={lora_rank}, lora_alpha={lora_alpha}")

# Create torchtune config and run
os.system("""tune run lora_finetune_single_device \\
    --config llama3_2/1B_lora_single_device \\
    model.path=/workspace/model \\
    dataset.source=/workspace/dataset \\
    batch_size={batch_size} \\
    epochs={epochs} \\
    lora_rank={lora_rank} \\
    lora_alpha={lora_alpha}
""")
'''

            def train_func():
                exec(training_script)  # noqa: S102

            trainer = CustomTrainer(  # type: ignore[assignment]
                func=train_func,
                packages_to_install=[
                    "torchtune",
                    "transformers",
                    "datasets",
                    "huggingface_hub",
                    "accelerate",
                ],
                num_nodes=num_nodes,
                env={"HF_TOKEN": hf_token} if hf_token else None,
            )
            job_name = client.train(
                runtime=runtime,
                trainer=trainer,
                options=options if options else None,
            )

        return ToolResponse(
            data={
                "job_name": job_name,
                "status": "Created",
                "message": f"Training job '{job_name}' submitted successfully",
            }
        ).model_dump()

    except Exception as e:
        # Extract detailed error info for debugging
        error_msg = str(e)
        details: dict[str, Any] | None = None

        # Try to get more context from exception chain
        if e.__cause__:
            details = {"cause": str(e.__cause__)}
        elif hasattr(e, "response"):
            # Kubernetes API errors often have response body
            try:
                details = {"response": e.response.text}  # type: ignore[union-attr]
            except Exception:
                pass

        return ToolError(
            error=error_msg,
            error_code=ErrorCode.SDK_ERROR,
            details=details,
            hint="Use troubleshooting_guide prompt for diagnosis, or resource_planning to check requirements",
        ).model_dump()


def run_custom_training(
    script: str,
    name: str | None = None,
    num_nodes: int = 1,
    gpu_per_node: int = 1,
    packages: list[str] | None = None,
    # Runtime patches
    node_selector: dict[str, str] | None = None,
    tolerations: list[dict[str, Any]] | None = None,
    env: list[dict[str, Any]] | None = None,
    volumes: list[dict[str, Any]] | None = None,
    volume_mounts: list[dict[str, Any]] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Run a custom Python training script on the cluster.

    Script is validated for security before execution.

    Args:
        script: Python code string. Validated against dangerous operations.
        name: TrainJob name. Auto-generated if not provided.
        num_nodes: Distributed training nodes. Defaults to 1.
        gpu_per_node: GPUs per node. Set 0 for CPU-only. Defaults to 1.
        packages: Pip packages to install (e.g., ``["torch", "transformers"]``).
        node_selector: K8s node selector.
        tolerations: K8s tolerations.
        env: Environment variables as list of dicts.
        volumes: K8s volume definitions.
        volume_mounts: K8s volume mounts.
        confirmed: Set ``True`` to submit. ``False`` returns preview.

    Returns:
        dict: If ``confirmed=False``: preview with truncated script.
            If ``confirmed=True``: ``job_name``, ``status``, ``message``.

    Note:
        Use ``run_container_training()`` for unrestricted script execution.
    """
    try:
        if not _SDK_AVAILABLE:
            return ToolError(
                error="Kubeflow SDK not available",
                error_code=ErrorCode.SDK_ERROR,
            ).model_dump()

        safe, reason = is_safe_python_code(script)
        if not safe:
            return ToolError(
                error=f"Script validation failed: {reason}",
                error_code=ErrorCode.VALIDATION_ERROR,
                hint="Use custom_training_workflow prompt for secure script guidelines, or run_container_training for unrestricted access",
            ).model_dump()

        if name:
            err = validate_k8s_name(name)
            if err:
                return err.model_dump()

        config: dict[str, Any] = {
            "script": script[:200] + "..." if len(script) > 200 else script,
            "name": name,
            "num_nodes": num_nodes,
            "gpu_per_node": gpu_per_node,
            "packages": packages or [],
        }

        # Add runtime patches to preview if specified
        if node_selector:
            config["node_selector"] = node_selector
        if tolerations:
            config["tolerations"] = tolerations
        if env:
            config["env"] = env
        if volumes:
            config["volumes"] = volumes
        if volume_mounts:
            config["volume_mounts"] = volume_mounts

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        # Create a function that executes the script
        def train_func():
            exec(script)  # noqa: S102

        trainer = CustomTrainer(
            func=train_func,
            packages_to_install=packages,
            num_nodes=num_nodes,
            resources_per_node={"gpu": gpu_per_node} if gpu_per_node > 0 else None,
        )

        # Build runtime patch options if any patches specified
        options = _build_runtime_patch(
            node_selector=node_selector,
            tolerations=tolerations,
            env=env,
            volumes=volumes,
            volume_mounts=volume_mounts,
        )

        client = get_trainer_client()
        job_name = client.train(trainer=trainer, options=options if options else None)

        return ToolResponse(
            data={
                "job_name": job_name,
                "status": "Created",
                "message": f"Custom training job '{job_name}' submitted",
            }
        ).model_dump()

    except Exception as e:
        error_msg = str(e)
        details: dict[str, Any] | None = None
        if e.__cause__:
            details = {"cause": str(e.__cause__)}
        elif hasattr(e, "response"):
            try:
                details = {"response": e.response.text}  # type: ignore[union-attr]
            except Exception:
                pass
        return ToolError(
            error=error_msg,
            error_code=ErrorCode.SDK_ERROR,
            details=details,
            hint="Use troubleshooting_guide prompt for diagnosis",
        ).model_dump()


def run_container_training(
    image: str,
    command: list[str] | None = None,
    num_nodes: int = 1,
    gpu_per_node: int = 1,
    env: dict[str, str] | None = None,
    node_selector: dict[str, str] | None = None,
    tolerations: list[dict[str, Any]] | None = None,
    volumes: list[dict[str, Any]] | None = None,
    volume_mounts: list[dict[str, Any]] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Run training with a pre-built container image.

    No script validation - full control via container ENTRYPOINT/CMD.

    Args:
        image: Container image (e.g., ``pytorch/pytorch:2.0-cuda11.8``).
        command: Override container command (baked into image if omitted).
        num_nodes: Distributed training nodes. Defaults to 1.
        gpu_per_node: GPUs per node. Set 0 for CPU-only. Defaults to 1.
        env: Environment variables as dict (e.g., ``{"HF_TOKEN": "xxx"}``).
        node_selector: K8s node selector.
        tolerations: K8s tolerations.
        volumes: K8s volumes (e.g., ``[{"name": "data", "persistentVolumeClaim": {...}}]``).
        volume_mounts: K8s mounts (e.g., ``[{"name": "data", "mountPath": "/data"}]``).
        confirmed: Set ``True`` to submit. ``False`` returns preview.

    Returns:
        dict: If ``confirmed=False``: preview with config.
            If ``confirmed=True``: ``job_name``, ``status``, ``message``.
    """
    try:
        if not _SDK_AVAILABLE:
            return ToolError(
                error="Kubeflow SDK not available",
                error_code=ErrorCode.SDK_ERROR,
            ).model_dump()

        config: dict[str, Any] = {
            "image": image,
            "command": command,
            "num_nodes": num_nodes,
            "gpu_per_node": gpu_per_node,
            "env": env,
        }

        # Add runtime patches to preview if specified
        if node_selector:
            config["node_selector"] = node_selector
        if tolerations:
            config["tolerations"] = tolerations
        if volumes:
            config["volumes"] = volumes
        if volume_mounts:
            config["volume_mounts"] = volume_mounts

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        # Note: SDK 0.4.0 CustomTrainerContainer doesn't support custom command
        # The command should be baked into the container image's ENTRYPOINT/CMD
        trainer = CustomTrainerContainer(
            image=image,
            num_nodes=num_nodes,
            resources_per_node={"gpu": gpu_per_node} if gpu_per_node > 0 else None,
            env=env,
        )

        # Build runtime patch options if any patches specified
        # Convert env dict to list format for patches
        env_list = [{"name": k, "value": v} for k, v in (env or {}).items()] if env else None
        options = _build_runtime_patch(
            node_selector=node_selector,
            tolerations=tolerations,
            env=env_list,
            volumes=volumes,
            volume_mounts=volume_mounts,
        )

        client = get_trainer_client()
        job_name = client.train(trainer=trainer, options=options if options else None)

        return ToolResponse(
            data={
                "job_name": job_name,
                "status": "Created",
                "message": f"Container training job '{job_name}' submitted",
            }
        ).model_dump()

    except Exception as e:
        error_msg = str(e)
        details: dict[str, Any] | None = None
        if e.__cause__:
            details = {"cause": str(e.__cause__)}
        elif hasattr(e, "response"):
            try:
                details = {"response": e.response.text}  # type: ignore[union-attr]
            except Exception:
                pass
        return ToolError(
            error=error_msg,
            error_code=ErrorCode.SDK_ERROR,
            details=details,
            hint="Use troubleshooting_guide prompt for diagnosis",
        ).model_dump()

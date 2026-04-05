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

"""SDK client factories with caching and timeout configuration.

Mirrors kubeflow SDK's client structure:
- TrainerClient from kubeflow.trainer
"""

from functools import lru_cache
from typing import TYPE_CHECKING

# Import at module level to avoid import deadlocks when tools are called rapidly
from kubeflow.trainer import TrainerClient

if TYPE_CHECKING:
    from kubernetes import client as k8s_client

# Strict timeout for K8s API calls (seconds)
K8S_TIMEOUT = 5


def configure_k8s_client() -> "k8s_client.ApiClient":
    """Configure K8s client with strict timeouts.

    Returns:
        Configured ApiClient with timeout settings
    """
    from kubernetes import client, config

    config.load_config()
    configuration = client.Configuration.get_default_copy()
    configuration.retries = 1
    api_client = client.ApiClient(configuration)
    return api_client


def get_core_v1_api() -> "k8s_client.CoreV1Api":
    """Get CoreV1Api with timeout configuration."""
    from kubernetes import client

    api_client = configure_k8s_client()
    return client.CoreV1Api(api_client)


def get_custom_objects_api() -> "k8s_client.CustomObjectsApi":
    """Get CustomObjectsApi with timeout configuration."""
    from kubernetes import client

    api_client = configure_k8s_client()
    return client.CustomObjectsApi(api_client)


@lru_cache(maxsize=1)
def get_trainer_client() -> TrainerClient:
    """Get or create TrainerClient singleton.

    Uses default KubernetesBackendConfig with current kubeconfig context.
    """
    return TrainerClient()


def reset_clients() -> None:
    """Reset cached clients (for testing)."""
    get_trainer_client.cache_clear()

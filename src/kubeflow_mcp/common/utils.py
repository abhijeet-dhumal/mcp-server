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

"""SDK client factories with caching.

Mirrors kubeflow SDK's client structure:
- TrainerClient from kubeflow.trainer
"""

from functools import lru_cache

# Import at module level to avoid import deadlocks when tools are called rapidly
from kubeflow.trainer import TrainerClient


@lru_cache(maxsize=1)
def get_trainer_client() -> TrainerClient:
    """Get or create TrainerClient singleton.

    Uses default KubernetesBackendConfig with current kubeconfig context.
    """
    return TrainerClient()


def reset_clients() -> None:
    """Reset cached clients (for testing)."""
    get_trainer_client.cache_clear()

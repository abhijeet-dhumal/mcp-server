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

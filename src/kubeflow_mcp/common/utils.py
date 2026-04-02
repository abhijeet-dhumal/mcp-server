"""SDK client factories with caching.

Mirrors kubeflow SDK's client structure:
- TrainerClient from kubeflow.trainer
"""

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kubeflow.trainer import TrainerClient


@lru_cache(maxsize=1)
def get_trainer_client() -> "TrainerClient":
    """Get or create TrainerClient singleton.

    Uses default KubernetesBackendConfig with current kubeconfig context.
    """
    from kubeflow.trainer import TrainerClient

    return TrainerClient()


def reset_clients() -> None:
    """Reset cached clients (for testing)."""
    get_trainer_client.cache_clear()

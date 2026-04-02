"""Kubernetes authentication interface.

NOTE: This is an interface placeholder for Stage 1.
Actual implementation deferred to production hardening.
"""

from dataclasses import dataclass


@dataclass
class AuthContext:
    """Authentication context for requests."""

    user: str | None = None
    groups: list[str] | None = None
    impersonate: str | None = None


def get_auth_context() -> AuthContext:
    """Get current authentication context.

    Returns default context. Full implementation requires:
    - K8s service account token validation
    - User impersonation support
    - RBAC integration
    """
    return AuthContext()

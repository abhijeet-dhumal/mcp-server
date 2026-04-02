"""Error codes and status constants."""


class ErrorCode:
    """Standard error codes for tool responses."""

    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    KUBERNETES_ERROR = "KUBERNETES_ERROR"
    SDK_ERROR = "SDK_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    TIMEOUT = "TIMEOUT"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    RATE_LIMITED = "RATE_LIMITED"


class JobStatus:
    """Training job status constants."""

    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    SUSPENDED = "Suspended"

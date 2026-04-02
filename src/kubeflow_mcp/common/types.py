"""Shared types for kubeflow-mcp tools."""

from typing import Any, Literal

from pydantic import BaseModel


class ToolResponse(BaseModel):
    """Standard success response."""

    success: Literal[True] = True
    data: dict[str, Any]


class ToolError(BaseModel):
    """Standard error response."""

    success: Literal[False] = False
    error: str
    error_code: str | None = None
    details: dict[str, Any] | None = None


class PreviewResponse(BaseModel):
    """Response for two-phase confirmation pattern."""

    status: Literal["preview"] = "preview"
    message: str = "Set confirmed=True to execute"
    config: dict[str, Any]


ToolResult = ToolResponse | ToolError | PreviewResponse

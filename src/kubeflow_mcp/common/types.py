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
    hint: str | None = None  # Suggest relevant MCP prompt for recovery


class PreviewResponse(BaseModel):
    """Response for two-phase confirmation pattern."""

    status: Literal["preview"] = "preview"
    message: str = "Set confirmed=True to execute"
    config: dict[str, Any]


ToolResult = ToolResponse | ToolError | PreviewResponse

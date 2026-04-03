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

"""Centralized constants for the kubeflow-mcp server.

This module is the single source of truth for:
- Error codes and job statuses
- MCP prompt metadata (names, descriptions)
- MCP resource metadata (URIs, descriptions)
- Tool phase categorization

Import from here to ensure consistency across the codebase.
"""


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


# =============================================================================
# MCP Prompt Metadata
# Single source of truth for prompt names and descriptions.
# Used by: server.py (SERVER_INSTRUCTIONS), prompts.py (registration)
# =============================================================================

PROMPT_METADATA: dict[str, str] = {
    "fine_tuning_workflow": "Step-by-step fine-tuning guide",
    "custom_training_workflow": "Custom script/container guide",
    "troubleshooting_guide": "Diagnose and fix failures",
    "resource_planning": "Plan resources before training",
    "monitoring_workflow": "Monitor jobs and debug issues",
}


# =============================================================================
# MCP Resource Metadata
# Single source of truth for resource URIs and descriptions.
# Used by: server.py (SERVER_INSTRUCTIONS), resources.py (registration)
# =============================================================================

RESOURCE_METADATA: dict[str, str] = {
    "trainer://models/supported": "Tested model configurations",
    "trainer://runtimes/info": "Runtime documentation",
    "trainer://guides/quickstart": "Quick start guide",
    "trainer://guides/troubleshooting": "Troubleshooting quick reference",
}


# =============================================================================
# Tool Phase Categories
# Maps tools to their workflow phase for tagging and discovery.
# Used by: server.py (TOOL_ANNOTATIONS), dynamic_tools.py (TOOL_HIERARCHY)
# =============================================================================

TOOL_PHASES: dict[str, list[str]] = {
    "planning": ["get_cluster_resources", "estimate_resources"],
    "discovery": [
        "list_training_jobs",
        "get_training_job",
        "list_runtimes",
        "get_runtime",
        "get_runtime_packages",
    ],
    "training": ["fine_tune", "run_custom_training", "run_container_training"],
    "monitoring": ["get_training_logs", "get_training_events", "wait_for_training"],
    "lifecycle": ["delete_training_job", "suspend_training_job", "resume_training_job"],
}

# Reverse mapping: tool name -> phase
TOOL_TO_PHASE: dict[str, str] = {
    tool: phase for phase, tools in TOOL_PHASES.items() for tool in tools
}

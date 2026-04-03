"""MCP server factory with dynamic client loading.

Designed for extensibility:
- Phase 1: trainer only
- Phase 2+: Contributors add optimizer, hub
"""

import importlib
import logging

from fastmcp import FastMCP

from kubeflow_mcp.core.health import HealthManager
from kubeflow_mcp.core.policy import get_allowed_tools
from kubeflow_mcp.core.resources import register_skill_resources

logger = logging.getLogger(__name__)

CLIENT_MODULES = {
    "trainer": "kubeflow_mcp.trainer",
    "optimizer": "kubeflow_mcp.optimizer",
    "hub": "kubeflow_mcp.hub",
}

SERVER_INSTRUCTIONS = """
Kubeflow MCP Server - AI Model Training on Kubernetes

CRITICAL WORKFLOW - Follow these steps IN ORDER:

1. PLANNING (always do first):
   - get_cluster_resources() → Check GPU availability
   - estimate_resources(model) → Check memory requirements
   - If gpu_total=0 or insufficient memory, STOP and inform user

2. DISCOVERY (if needed):
   - list_runtimes() → Find available training runtimes
   - list_training_jobs() → See existing jobs

3. TRAINING (requires user confirmation):
   - fine_tune(..., confirmed=False) → Preview config first
   - Show preview to user, ask for confirmation
   - fine_tune(..., confirmed=True) → Submit job only after approval

4. MONITORING:
   - get_training_job(job_id) → Check status
   - get_training_logs(job_id) → View output/errors
   - get_training_events(job_id) → Debug scheduling issues

TOOL SELECTION:
- HuggingFace model fine-tuning → fine_tune()
- Custom Python training script → run_custom_training()
- Pre-built container image → run_container_training()

IMPORTANT:
- NEVER skip planning steps before training
- ALWAYS preview before submitting (confirmed=False first)
- Training jobs consume GPU resources - be conservative
- Use get_training_events() to debug stuck/failed jobs

For detailed guides, read the skill resources:
- trainer://skills/fine-tuning → Fine-tuning workflow
- trainer://skills/troubleshooting → Error recovery
"""


def create_server(
    clients: list[str] | None = None,
    persona: str = "ml-engineer",
) -> FastMCP:
    """Create MCP server with dynamic client loading.

    Args:
        clients: List of client modules to load (default: ["trainer"])
                 Options: "trainer", "optimizer", "hub"
        persona: User role for tool filtering

    Returns:
        Configured FastMCP server instance
    """
    mcp: FastMCP = FastMCP("kubeflow-mcp", instructions=SERVER_INSTRUCTIONS)
    allowed_tools = get_allowed_tools(persona)

    if clients is None:
        clients = ["trainer"]

    for client_name in clients:
        if client_name not in CLIENT_MODULES:
            logger.warning(f"Unknown client: {client_name}, skipping")
            continue

        try:
            module = importlib.import_module(CLIENT_MODULES[client_name])

            if not hasattr(module, "TOOLS") or not module.TOOLS:
                logger.info(f"Client '{client_name}' has no tools (stub module)")
                continue

            registered = 0
            for tool_func in module.TOOLS:
                tool_name = tool_func.__name__

                if allowed_tools is None or tool_name in allowed_tools:
                    mcp.tool()(tool_func)
                    registered += 1
                    logger.debug(f"Registered tool: {tool_name}")

            logger.info(f"Loaded client '{client_name}' with {registered} tools")

        except ImportError as e:
            logger.error(f"Failed to load client '{client_name}': {e}")

    register_skill_resources(mcp, clients)

    health = HealthManager(mcp)
    health.register_health_tools()

    return mcp

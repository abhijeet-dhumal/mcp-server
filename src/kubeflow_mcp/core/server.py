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
    mcp = FastMCP("kubeflow-mcp")
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

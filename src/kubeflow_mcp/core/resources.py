"""MCP resource registration for skills."""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)

SKILLS_DIR = os.getenv("KUBEFLOW_MCP_SKILLS_DIR", "skills")


def register_skill_resources(mcp: "FastMCP", clients: list[str]) -> None:
    """Register skill files as MCP resources.

    Skills are markdown instruction files that LLMs read to understand
    how to use tools effectively.

    Args:
        mcp: FastMCP server instance
        clients: List of enabled client modules
    """
    skills_path = Path(SKILLS_DIR)
    if not skills_path.exists():
        logger.debug(f"Skills directory not found: {skills_path}")
        return

    registered = 0
    for client in clients:
        client_skills = skills_path / client
        if not client_skills.exists():
            continue

        for skill_file in client_skills.glob("*.md"):
            resource_uri = f"skill://{client}/{skill_file.stem}"

            try:

                @mcp.resource(resource_uri)
                def read_skill(path: Path = skill_file) -> str:
                    return path.read_text()

                registered += 1
                logger.debug(f"Registered skill: {resource_uri}")

            except Exception as e:
                logger.warning(f"Failed to register skill {skill_file}: {e}")

    if registered:
        logger.info(f"Registered {registered} skill resources")

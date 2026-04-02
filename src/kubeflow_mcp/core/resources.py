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
    how to use tools effectively. They can be accessed via:
    - File reference: @skills/trainer/SKILL.md
    - MCP resource: skill://trainer/SKILL (if supported)

    Args:
        mcp: FastMCP server instance
        clients: List of enabled client modules
    """
    skills_path = Path(SKILLS_DIR)
    if not skills_path.exists():
        logger.debug(f"Skills directory not found: {skills_path}")
        return

    available_skills = []
    for client in clients:
        client_skills = skills_path / client
        if not client_skills.exists():
            continue

        for skill_file in client_skills.glob("*.md"):
            available_skills.append(f"{client}/{skill_file.name}")

    if available_skills:
        logger.info(f"Available skills: {', '.join(available_skills)}")

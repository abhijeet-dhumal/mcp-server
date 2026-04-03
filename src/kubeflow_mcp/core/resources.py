"""MCP resource registration for skills."""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)

SKILLS_DIR = os.getenv("KUBEFLOW_MCP_SKILLS_DIR", "skills")


def _get_skills_base_path() -> Path:
    """Get the skills directory path.

    Searches in order:
    1. KUBEFLOW_MCP_SKILLS_DIR env var
    2. ./skills (relative to cwd)
    3. Package directory/skills
    """
    # Check env var first
    if env_path := os.getenv("KUBEFLOW_MCP_SKILLS_DIR"):
        return Path(env_path)

    # Check relative to cwd
    cwd_skills = Path.cwd() / "skills"
    if cwd_skills.exists():
        return cwd_skills

    # Check relative to package
    package_dir = Path(__file__).parent.parent.parent.parent
    package_skills = package_dir / "skills"
    if package_skills.exists():
        return package_skills

    return Path(SKILLS_DIR)


def register_skill_resources(mcp: "FastMCP", clients: list[str]) -> None:
    """Register skill files as MCP resources for on-demand loading.

    Skills are markdown instruction files that LLMs can read to understand
    how to use tools effectively. They are registered as MCP resources
    with URIs like: trainer://skills/fine-tuning

    This follows the progressive disclosure pattern:
    - Server instructions provide workflow summary (always loaded)
    - Skills provide detailed guides (loaded on demand via resources/read)

    Args:
        mcp: FastMCP server instance
        clients: List of enabled client modules
    """
    skills_path = _get_skills_base_path()
    if not skills_path.exists():
        logger.debug(f"Skills directory not found: {skills_path}")
        return

    registered_count = 0

    for client in clients:
        client_skills = skills_path / client
        if not client_skills.exists():
            continue

        for skill_file in client_skills.glob("*.md"):
            skill_name = skill_file.stem.lower()
            resource_uri = f"{client}://skills/{skill_name}"

            # Create a closure to capture the file path
            def make_resource_handler(file_path: Path):
                def handler() -> str:
                    try:
                        return file_path.read_text(encoding="utf-8")
                    except Exception as e:
                        return f"Error reading skill: {e}"

                return handler

            # Register as MCP resource
            try:
                # Get description from first line of file
                first_line = skill_file.read_text(encoding="utf-8").split("\n")[0]
                description = first_line.lstrip("# ").strip()[:100]

                mcp.resource(resource_uri, description=description)(
                    make_resource_handler(skill_file)
                )
                registered_count += 1
                logger.debug(f"Registered skill resource: {resource_uri}")
            except Exception as e:
                logger.warning(f"Failed to register skill {resource_uri}: {e}")

    if registered_count > 0:
        logger.info(f"Registered {registered_count} skill resources")

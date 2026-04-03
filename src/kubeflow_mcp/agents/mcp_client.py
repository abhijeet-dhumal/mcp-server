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

"""MCP client for local agents.

Provides a standardized interface for local agents to access kubeflow-mcp
server via the MCP protocol. This ensures the same tools and prompts are
available whether using Cursor, Claude Desktop, or the local Ollama agent.

Usage:
    from kubeflow_mcp.agents.mcp_client import MCPAgentClient

    client = MCPAgentClient()
    await client.connect()
    tools = await client.get_tools()
    prompts = await client.list_prompts()
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class MCPAgentClient:
    """MCP client for local agents using in-process server.

    This client creates an in-process MCP server and provides async methods
    to access tools and prompts. This is the standardized way for local agents
    to interact with kubeflow-mcp.
    """

    _server: "FastMCP[Any] | None"

    def __init__(self, persona: str = "ml-engineer"):
        """Initialize MCP client.

        Args:
            persona: User persona for tool filtering
        """
        self.persona = persona
        self._server = None
        self._client = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to the MCP server (in-process)."""
        if self._connected:
            return

        # Import here to avoid circular imports
        from kubeflow_mcp.core.server import create_server

        # Create server instance
        self._server = create_server(clients=["trainer"], persona=self.persona)

        # For in-process usage, we access tools directly from the server
        # This avoids the complexity of subprocess management while still
        # using the same server configuration
        self._connected = True
        logger.debug(f"MCP client connected with persona: {self.persona}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        self._server = None
        self._client = None
        self._connected = False

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server.

        Returns:
            List of tool definitions with name, description, and parameters
        """
        if not self._connected:
            await self.connect()

        if self._server is None:
            return []

        # Use FastMCP's public API
        mcp_tools = await self._server.list_tools()
        tools = []
        for tool in mcp_tools:
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": getattr(tool, "parameters", {}),
                }
            )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self._connected:
            await self.connect()

        if self._server is None:
            raise RuntimeError("Server not connected")

        # Use FastMCP's public API
        tool = await self._server.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        # Call the tool function (FastMCP tools have .fn attribute)
        if hasattr(tool, "fn") and tool.fn:
            result = tool.fn(**arguments)
            # Handle async functions
            if hasattr(result, "__await__"):
                result = await result
            return result
        raise ValueError(f"Tool {name} has no callable function")

    async def list_prompts(self) -> list[dict[str, Any]]:
        """List available prompts from the MCP server.

        Returns:
            List of prompt definitions with name and description
        """
        if not self._connected:
            await self.connect()

        if self._server is None:
            return []

        # Use FastMCP's public API
        mcp_prompts = await self._server.list_prompts()
        prompts = []
        for prompt in mcp_prompts:
            prompts.append(
                {
                    "name": prompt.name,
                    "description": getattr(prompt, "description", ""),
                }
            )
        return prompts

    async def get_prompt(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        """Get a rendered prompt from the MCP server.

        Args:
            name: Prompt name
            arguments: Prompt arguments

        Returns:
            Rendered prompt content
        """
        if not self._connected:
            await self.connect()

        if self._server is None:
            raise RuntimeError("Server not connected")

        # Use FastMCP's public API
        prompt = await self._server.get_prompt(name)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")

        # Render the prompt with arguments (FastMCP prompts have .fn attribute)
        args = arguments or {}
        if hasattr(prompt, "fn") and prompt.fn:
            result = prompt.fn(**args)
            if hasattr(result, "__await__"):
                result = await result
            return str(result)
        raise ValueError(f"Prompt {name} has no callable function")

    def get_tools_sync(self) -> list[dict[str, Any]]:
        """Synchronous wrapper for list_tools."""
        return asyncio.get_event_loop().run_until_complete(self.list_tools())

    def call_tool_sync(self, name: str, arguments: dict[str, Any]) -> Any:
        """Synchronous wrapper for call_tool."""
        return asyncio.get_event_loop().run_until_complete(self.call_tool(name, arguments))


def get_mcp_tools_for_llamaindex(persona: str = "ml-engineer"):
    """Get LlamaIndex FunctionTools from MCP server.

    This function creates tools that use the MCP client to call the server,
    ensuring standardized access to all kubeflow-mcp functionality.

    Args:
        persona: User persona for tool filtering

    Returns:
        List of LlamaIndex FunctionTool instances
    """
    import asyncio

    try:
        from llama_index.core.tools import FunctionTool
    except ImportError as e:
        raise ImportError("llama-index-core is required. Run: uv sync --extra agents") from e

    # Import here to avoid circular imports
    from kubeflow_mcp.core.server import create_server

    # Create server and extract tools using public API
    server = create_server(clients=["trainer"], persona=persona)
    mcp_tools = asyncio.get_event_loop().run_until_complete(server.list_tools())

    tools = []
    for mcp_tool in mcp_tools:
        # Get the full tool with function reference
        full_tool = asyncio.get_event_loop().run_until_complete(server.get_tool(mcp_tool.name))
        if full_tool and hasattr(full_tool, "fn") and full_tool.fn:
            func_tool = FunctionTool.from_defaults(
                fn=full_tool.fn,
                name=mcp_tool.name,
                description=mcp_tool.description or mcp_tool.name,
            )
            tools.append(func_tool)

    logger.info(f"Loaded {len(tools)} tools from MCP server")
    return tools


def get_mcp_prompts(persona: str = "ml-engineer") -> dict[str, Any]:
    """Get prompts from MCP server.

    Args:
        persona: User persona

    Returns:
        Dictionary mapping prompt names to their render functions
    """
    import asyncio

    from kubeflow_mcp.core.server import create_server

    server = create_server(clients=["trainer"], persona=persona)
    mcp_prompts = asyncio.get_event_loop().run_until_complete(server.list_prompts())

    prompts = {}
    for mcp_prompt in mcp_prompts:
        # Get the full prompt with function reference
        full_prompt = asyncio.get_event_loop().run_until_complete(
            server.get_prompt(mcp_prompt.name)
        )
        if full_prompt and hasattr(full_prompt, "fn"):
            prompts[mcp_prompt.name] = {
                "description": getattr(mcp_prompt, "description", ""),
                "fn": full_prompt.fn,
            }

    logger.info(f"Loaded {len(prompts)} prompts from MCP server")
    return prompts

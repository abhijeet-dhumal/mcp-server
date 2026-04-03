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

"""Ollama agent using LlamaIndex FunctionAgent with native tool calling.

Requires optional dependencies:
    uv sync --extra agents
    pip install kubeflow-mcp[agents]

Usage:
    ollama serve
    uv run python -m kubeflow_mcp.agents.ollama
    uv run python -m kubeflow_mcp.agents.ollama --model qwen2.5:7b
"""

import io
import json
import logging
import sys
from typing import Any

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("llama_index").setLevel(logging.ERROR)

try:
    from llama_index.core.agent.workflow import FunctionAgent
    from llama_index.core.memory import ChatMemoryBuffer
    from llama_index.core.tools import FunctionTool
    from llama_index.llms.ollama import Ollama
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    sys.exit("Error: required packages not installed\nRun: uv sync --extra agents")

# Optional MCP client support
MCP_CLIENT_AVAILABLE = False
try:
    from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

    MCP_CLIENT_AVAILABLE = True
except ImportError:
    pass  # MCP client optional, fall back to direct imports

from kubeflow_mcp.agents.dynamic_tools import (  # noqa: E402
    get_dynamic_system_prompt,
    get_dynamic_tools,
)

# Try to import TOOLS directly (fallback mode)
try:
    from kubeflow_mcp.trainer import TOOLS  # noqa: E402
except ImportError:
    TOOLS = []  # Will use MCP client instead

from kubeflow_mcp.core.server import SERVER_INSTRUCTIONS  # noqa: E402

console = Console()

DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_URL = "http://localhost:11434"

# Import tool registries for dynamic counts
from kubeflow_mcp.agents.dynamic_tools import PROGRESSIVE_TOOLS, SEMANTIC_TOOLS  # noqa: E402
from kubeflow_mcp.trainer import TOOLS  # noqa: E402

# Tool modes - counts computed dynamically from actual registries
_NUM_TOOLS = len(TOOLS)
_NUM_PROGRESSIVE = len(PROGRESSIVE_TOOLS)
_NUM_SEMANTIC = len(SEMANTIC_TOOLS)

# User-facing tool modes
# "full" uses MCP protocol (with fallback to direct import)
# "progressive" and "semantic" reduce token usage via meta-tools
TOOL_MODES = {
    "full": f"All {_NUM_TOOLS} tools via MCP protocol",
    "progressive": f"{_NUM_PROGRESSIVE} meta-tools with hierarchical discovery",
    "semantic": f"{_NUM_SEMANTIC} meta-tools with embedding search",
}

# Legacy aliases for backward compatibility
_MODE_ALIASES = {"static": "full", "mcp": "full"}

# Agent-specific additions to server instructions
AGENT_HINTS = """
AGENT-SPECIFIC:
- When greeted, introduce yourself briefly and offer to help with training tasks
- Model ID formats: estimate_resources() uses "google/gemma-2b", fine_tune() uses "hf://google/gemma-2b"
- Execute planning steps (1-4) together, only pause after showing the preview
- If no GPUs (gpu_total=0), suggest CPU training or inform user
"""

# Use server instructions as base, add agent-specific hints
SYSTEM_PROMPT_FULL = SERVER_INSTRUCTIONS + AGENT_HINTS
SYSTEM_PROMPT = SYSTEM_PROMPT_FULL


async def create_mcp_stdio_client(
    server_command: list[str] | None = None,
) -> tuple[Any, list[FunctionTool], str]:
    """Create MCP client via stdio protocol (standard MCP approach).

    This spawns the kubeflow-mcp server as a subprocess and connects via stdio,
    the same way Cursor IDE and Claude Desktop connect. This ensures the local
    agent uses the exact same protocol and gets identical behavior.

    Args:
        server_command: Command to start the MCP server.
                       Default: ["kubeflow-mcp", "serve", "--transport", "stdio"]

    Returns:
        Tuple of (mcp_client, tools, instructions)
    """
    if not MCP_CLIENT_AVAILABLE:
        raise ImportError("llama-index-tools-mcp not installed. Run: uv sync --extra agents")

    if server_command is None:
        server_command = ["kubeflow-mcp", "serve", "--transport", "stdio"]

    client = BasicMCPClient(server_command)
    tool_spec = McpToolSpec(client=client)

    # Get tools from server via MCP protocol
    tools = await tool_spec.ato_tool_list()

    # Get server instructions (for system prompt)
    instructions = ""
    try:
        # Access the MCP session to get server info
        if hasattr(client, "session") and client.session:
            server_info = await client.session.get_server_info()
            if hasattr(server_info, "instructions") and server_info.instructions:
                instructions = server_info.instructions
    except Exception:
        pass  # Fall back to default prompt

    return client, tools, instructions


def create_tools_fallback() -> tuple[list[FunctionTool], str]:
    """Fallback: Load tools directly (in-process, no MCP protocol).

    Use this only when MCP client is not available or subprocess cannot be spawned.
    This is NOT the standard approach - prefer create_mcp_stdio_client().

    Returns:
        Tuple of (tools, instructions)
    """
    import asyncio

    from kubeflow_mcp.core.server import SERVER_INSTRUCTIONS, create_server

    mcp = create_server(clients=["trainer"])
    mcp_tools = asyncio.get_event_loop().run_until_complete(mcp.list_tools())

    tools = []
    for mcp_tool in mcp_tools:
        full_tool = asyncio.get_event_loop().run_until_complete(mcp.get_tool(mcp_tool.name))
        # FastMCP's FunctionTool has .fn attribute with the actual function
        if full_tool and hasattr(full_tool, "fn") and full_tool.fn:
            func_tool = FunctionTool.from_defaults(
                fn=full_tool.fn,  # type: ignore[union-attr]
                name=mcp_tool.name,
                description=mcp_tool.description or mcp_tool.name,
            )
            tools.append(func_tool)

    return tools, SERVER_INSTRUCTIONS


def create_tools(
    mode: str = "static",
) -> list[FunctionTool]:
    """Convert kubeflow-mcp tools to LlamaIndex FunctionTools.

    Args:
        mode: Tool loading mode:
            - "full": All tools via MCP protocol (~900 tokens) - default
            - "progressive": 3 meta-tools for hierarchical discovery (~85 tokens)
            - "semantic": 2 meta-tools for embedding search (~69 tokens)

    Note: For MCP mode, use create_mcp_client() async function instead.
    """
    # Dynamic modes use meta-tools
    if mode in ("progressive", "semantic"):
        tool_funcs = get_dynamic_tools(mode)
    elif mode == "mcp":
        raise ValueError("Use create_mcp_client() for MCP mode")
    else:
        if not TOOLS:
            raise ImportError("TOOLS not available. Use --mode mcp instead.")
        tool_funcs = TOOLS  # type: ignore[assignment]

    tools = []
    for tool_func in tool_funcs:
        doc = tool_func.__doc__ or ""
        desc = doc.split("\n")[0] if doc else tool_func.__name__

        func_tool = FunctionTool.from_defaults(
            fn=tool_func,  # type: ignore[arg-type]
            name=tool_func.__name__,
            description=desc,
        )
        tools.append(func_tool)
    return tools


def _format_tool_result(result: Any, max_lines: int = 15) -> str:
    """Format tool result for display, truncating if needed."""
    if isinstance(result, dict):
        formatted = json.dumps(result, indent=2, default=str)
    else:
        formatted = str(result)

    lines = formatted.split("\n")
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
    return formatted


class OllamaAgent:
    """Ollama agent using LlamaIndex FunctionAgent with thinking support.

    Supports multiple tool modes for different context budgets:
        - "full": All tools via MCP protocol (~900 tokens) - default, best accuracy
        - "progressive": 3 meta-tools (~85 tokens) - hierarchical discovery
        - "semantic": 2 meta-tools (~69 tokens) - embedding-based discovery
    """

    _agent: FunctionAgent | None
    _tools: list[FunctionTool] | None
    _thinking_supported: bool | None
    memory: ChatMemoryBuffer | None
    llm: Ollama | None
    _mcp_client: Any

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_URL,
        tool_mode: str = "full",
    ):
        self.model = model
        self.base_url = base_url
        # Resolve legacy aliases (static, mcp -> full)
        self.tool_mode = _MODE_ALIASES.get(tool_mode, tool_mode)
        self._agent = None
        self._tools = None
        self._thinking_supported = None  # None = unknown, True/False = tested
        self._use_thinking = True  # User preference
        self.memory = None
        self.llm = None
        self._mcp_client = None  # For MCP mode

        # Set system prompt based on mode
        if tool_mode in ("progressive", "semantic"):
            self._system_prompt = get_dynamic_system_prompt(tool_mode)
        else:
            # For static and mcp modes, use full prompt (mcp may override)
            self._system_prompt = SYSTEM_PROMPT_FULL

        # Dedicated event loop in background thread (prevents "Event loop is closed" errors)
        import asyncio
        import threading

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

    def _create_llm(self, with_thinking: bool):
        """Create Ollama LLM with or without thinking mode."""
        return Ollama(
            model=self.model,
            base_url=self.base_url,
            request_timeout=180.0,
            is_function_calling_model=True,
            thinking=with_thinking,
        )

    def _ensure_agent(self, with_thinking: bool | None = None):
        """Lazy initialization of agent."""
        if self._agent is not None:
            return

        if with_thinking is None:
            with_thinking = self._use_thinking

        # Suppress stderr during initialization
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        try:
            # Create tools based on mode
            if self.tool_mode == "full":
                self._init_mcp_agent(with_thinking)
            else:
                self._tools = create_tools(mode=self.tool_mode)
                self.llm = self._create_llm(with_thinking)
                # Larger memory for complex workflows (qwen3:8b has 32K context)
                self.memory = ChatMemoryBuffer.from_defaults(token_limit=16000)

                self._agent = FunctionAgent(
                    tools=self._tools,  # type: ignore[arg-type]
                    llm=self.llm,
                    memory=self.memory,
                    system_prompt=self._system_prompt,
                )
        finally:
            sys.stderr = old_stderr

    def _init_mcp_agent(self, with_thinking: bool):
        """Initialize agent via MCP stdio protocol (standard approach).

        Connects to kubeflow-mcp server via stdio, the same way Cursor IDE
        and Claude Desktop connect. This ensures protocol consistency and
        access to all MCP features (tools, prompts, resources).
        """
        import asyncio
        import concurrent.futures

        if not MCP_CLIENT_AVAILABLE:
            # Fallback to in-process if MCP client not available
            console.print("[yellow]MCP client not available, using fallback mode[/yellow]")
            self._tools, instructions = create_tools_fallback()
        else:
            # Standard MCP stdio connection (same as Cursor/Claude)
            future = asyncio.run_coroutine_threadsafe(create_mcp_stdio_client(), self._loop)
            try:
                self._mcp_client, self._tools, instructions = future.result(timeout=30)
            except concurrent.futures.TimeoutError as e:
                raise TimeoutError(
                    "MCP server connection timed out. "
                    "Ensure kubeflow-mcp is installed and accessible."
                ) from e
            except Exception as e:
                # Fallback if stdio connection fails
                console.print(f"[yellow]MCP connection failed ({e}), using fallback[/yellow]")
                self._tools, instructions = create_tools_fallback()

        # Use server instructions (same as external MCP clients get)
        if instructions:
            self._system_prompt = instructions + AGENT_HINTS

        self.llm = self._create_llm(with_thinking)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=16000)

        self._agent = FunctionAgent(
            tools=self._tools,  # type: ignore[arg-type]
            llm=self.llm,
            memory=self.memory,
            system_prompt=self._system_prompt,
        )

    def set_thinking_mode(self, enabled: bool):
        """Toggle thinking mode - recreates LLM but preserves memory."""
        if self._use_thinking == enabled:
            return

        self._use_thinking = enabled

        if self._agent is not None:
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                use_thinking = enabled and (self._thinking_supported is not False)
                self.llm = self._create_llm(use_thinking)
                self._agent = FunctionAgent(
                    tools=self._tools,  # type: ignore[arg-type]
                    llm=self.llm,
                    memory=self.memory,
                    system_prompt=self._system_prompt,
                )
            finally:
                sys.stderr = old_stderr

    def set_mode(self, mode: str) -> int:
        """Switch tool mode at runtime. Returns number of tools loaded."""
        # Handle legacy aliases (static, mcp -> full)
        resolved_mode = _MODE_ALIASES.get(mode, mode)

        if resolved_mode not in TOOL_MODES:
            raise ValueError(f"Unknown mode: {mode}. Choose from: {list(TOOL_MODES.keys())}")

        self.tool_mode = resolved_mode

        # Update system prompt based on mode
        if resolved_mode in ("progressive", "semantic"):
            self._system_prompt = get_dynamic_system_prompt(resolved_mode)
        else:
            self._system_prompt = SYSTEM_PROMPT_FULL

        # Force agent recreation with new tools
        self._agent = None
        self._tools = None
        self._ensure_agent(
            with_thinking=self._use_thinking and self._thinking_supported is not False
        )

        return len(self._tools) if self._tools else 0

    async def _chat_async(
        self,
        message: str,
        on_thinking=None,
        on_tool_call=None,
        on_tool_result=None,
    ) -> tuple[str, list[dict]]:
        """Async chat implementation with thinking support."""
        from llama_index.core.agent.workflow.workflow_events import (
            AgentOutput,
            AgentStream,
            ToolCallResult,
        )

        # Initialize with thinking if not yet tested
        if self._thinking_supported is None:
            self._ensure_agent(with_thinking=True)
        else:
            self._ensure_agent(with_thinking=self._thinking_supported and self._use_thinking)

        tool_calls = []
        seen_tools = set()

        try:
            assert self._agent is not None
            handler = self._agent.run(user_msg=message, memory=self.memory)

            async for event in handler.stream_events():
                if isinstance(event, AgentStream):
                    # Stream thinking output (attribute may not exist in all SDK versions)
                    thinking_delta = getattr(event, "thinking_delta", None)
                    if thinking_delta and on_thinking:
                        on_thinking(thinking_delta)

                    # Collect tool calls
                    if event.tool_calls:
                        for tc in event.tool_calls:
                            key = f"{tc.tool_name}:{json.dumps(tc.tool_kwargs, sort_keys=True)}"
                            if key not in seen_tools:
                                seen_tools.add(key)
                                tool_info = {"name": tc.tool_name, "args": tc.tool_kwargs}
                                tool_calls.append(tool_info)
                                if on_tool_call:
                                    on_tool_call(tool_info)

                elif isinstance(event, ToolCallResult):
                    if on_tool_result:
                        result_info = {
                            "name": event.tool_name,
                            "result": event.tool_output.content if event.tool_output else None,
                        }
                        on_tool_result(result_info)

            result = await handler
            if isinstance(result, AgentOutput):
                response = result.response.content or ""
            else:
                response = str(result)

            # Mark thinking as supported if we got here
            if self._thinking_supported is None:
                self._thinking_supported = True

        except Exception as e:
            error_msg = str(e)
            # Handle thinking mode not supported
            if "does not support thinking" in error_msg and self._thinking_supported is None:
                self._thinking_supported = False
                # Recreate agent without thinking
                self._agent = None
                self._ensure_agent(with_thinking=False)
                return await self._chat_async(message, on_thinking, on_tool_call, on_tool_result)
            raise

        return response, tool_calls

    def chat(
        self,
        message: str,
        on_thinking=None,
        on_tool_call=None,
        on_tool_result=None,
    ) -> tuple[str, list[dict]]:
        """Synchronous chat wrapper using dedicated event loop.

        Uses short polling intervals to allow Ctrl+C to interrupt.
        Includes retry logic for empty responses.
        """
        import asyncio

        def run_chat(msg: str) -> tuple[str, list[dict]]:
            future = asyncio.run_coroutine_threadsafe(
                self._chat_async(msg, on_thinking, on_tool_call, on_tool_result),
                self._loop,
            )
            while True:
                try:
                    return future.result(timeout=0.5)
                except TimeoutError:
                    continue
                except KeyboardInterrupt:
                    future.cancel()
                    raise

        response, tool_calls = run_chat(message)

        # Retry logic for empty responses
        if not response.strip() and not tool_calls:
            # Check if this was an action-oriented message
            action_words = ["yes", "proceed", "go", "ok", "start", "run", "train", "do it"]
            msg_lower = message.lower().strip()

            if any(word in msg_lower for word in action_words):
                console.print("[dim yellow]⚠ Empty response, retrying...[/dim yellow]")

                # Try disabling thinking mode (often causes empty responses)
                if self._use_thinking:
                    self.set_thinking_mode(False)

                # Retry with more explicit instruction
                retry_msg = f"Execute the action now: {message}"
                response, tool_calls = run_chat(retry_msg)

                # Second retry with even more explicit prompt
                if not response.strip() and not tool_calls:
                    retry_msg = "User confirmed. Call the appropriate tool to complete the task."
                    response, tool_calls = run_chat(retry_msg)

            # If still empty, provide helpful message
            if not response.strip() and not tool_calls:
                response = (
                    "I couldn't generate a response. Try:\n"
                    "- `/think` to toggle thinking mode\n"
                    "- Be more specific about what you want\n"
                    "- Use `/mode static` for more reliable responses"
                )

        return response, tool_calls

    def close(self):
        """Clean up agent resources."""
        try:
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            if self._loop_thread and self._loop_thread.is_alive():
                self._loop_thread.join(timeout=2)
        except Exception:
            pass  # Ignore cleanup errors


def _check_ollama_model(model: str, url: str) -> tuple[bool, str]:
    """Check if model exists on Ollama server."""
    import httpx

    try:
        response = httpx.get(f"{url}/api/tags", timeout=10.0)
        response.raise_for_status()
        available = [m["name"] for m in response.json().get("models", [])]

        if model in available:
            return True, "Model ready"

        # Check for similar models
        base = model.split(":")[0]
        similar = [m for m in available if m.startswith(base)]
        if similar:
            return False, f"Not found. Try: {', '.join(similar[:3])}"
        return False, f"Not found. Pull with: ollama pull {model}"

    except httpx.ConnectError:
        return False, f"Cannot connect to {url}"
    except Exception as e:
        return False, str(e)


def run_chat(
    model: str = DEFAULT_MODEL,
    url: str = DEFAULT_URL,
    tool_mode: str = "static",
):
    """Run interactive chat loop with rich UI.

    Args:
        model: Ollama model name
        url: Ollama server URL
        tool_mode: Tool loading mode:
            - "full": All tools via MCP protocol (~900 tokens) - default
            - "progressive": 3 meta-tools, hierarchical discovery (~85 tokens)
            - "semantic": 2 meta-tools, embedding search (~69 tokens)
    """
    # Welcome panel
    welcome = Table.grid(padding=(0, 1))
    welcome.add_column(justify="left")
    welcome.add_row(Text("Kubeflow Training Assistant", style="bold bright_cyan"))
    welcome.add_row(Text(f"Model: {model}", style="bright_green"))
    welcome.add_row(Text(f"Ollama: {url}", style="bright_white"))
    mode_desc = TOOL_MODES.get(tool_mode, tool_mode)
    welcome.add_row(Text(f"Tools: {mode_desc}", style="bright_yellow"))
    welcome.add_row()
    welcome.add_row(Text("Commands:", style="bright_yellow"))
    welcome.add_row(Text("  /tools       - List available tools", style="white"))
    welcome.add_row(
        Text("  /mode        - Switch tool mode (static/progressive/semantic)", style="white")
    )
    welcome.add_row(Text("  /think       - Toggle thinking output", style="white"))
    welcome.add_row(Text("  /file <path> - Read file and analyze it", style="white"))
    welcome.add_row(Text("  /clear       - Clear conversation memory", style="white"))
    welcome.add_row(Text("  exit         - Quit the agent", style="white"))

    console.print()
    console.print(
        Panel(
            welcome,
            title="[bold bright_white]🚀 Ollama Agent[/bold bright_white]",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )

    # Check model availability
    console.print("[bright_cyan]Checking model...[/bright_cyan]", end="\r")
    model_ok, model_msg = _check_ollama_model(model, url)
    if model_ok:
        console.print(f"[bright_green]✓ {model_msg}[/bright_green]          ")
    else:
        console.print(f"[bright_red]✗ {model_msg}[/bright_red]")
        return

    agent = OllamaAgent(model=model, base_url=url, tool_mode=tool_mode)

    # Pre-load agent
    console.print("[bright_cyan]Loading tools...[/bright_cyan]", end="\r")
    try:
        agent._ensure_agent()
        tools_count = len(agent._tools) if agent._tools else 0
        console.print(f"[bright_green]✓ Loaded {tools_count} tools[/bright_green]")
    except Exception as e:
        console.print(f"[bright_red]✗ Failed to initialize: {e}[/bright_red]")
        return

    console.print()
    console.print(
        "[bright_yellow]💡 Try: 'list training jobs' or 'check cluster resources'[/bright_yellow]"
    )

    # Enable readline for command history (up/down arrow navigation)
    try:
        import atexit
        import os
        import readline  # noqa: F401 - import enables history for input()

        # Optional: persist history across sessions
        history_file = os.path.expanduser("~/.kubeflow_mcp_history")
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        atexit.register(readline.write_history_file, history_file)
    except ImportError:
        pass  # readline not available on some platforms

    # State - thinking OFF by default, auto-enables after first message if model supports it
    show_thinking = False
    thinking_buffer: list[str] = []

    while True:
        try:
            console.print()
            console.print("[bold bright_blue]You →[/bold bright_blue] ", end="")
            user_input = input().strip()  # Use raw input() for readline history support

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                agent.close()
                console.print("[dim italic]Goodbye![/dim italic]")
                break

            if user_input.lower() == "/tools":
                tools = agent._tools or []
                console.print(f"\n[bold]Available tools ({len(tools)}):[/bold]")
                for t in tools:
                    console.print(f"  [bright_cyan]{t.metadata.name}[/bright_cyan]")
                continue

            if user_input.lower() == "/think":
                show_thinking = not show_thinking
                agent.set_thinking_mode(show_thinking)
                status = "ON" if show_thinking else "OFF"
                console.print(f"[bright_yellow]Thinking mode: {status}[/bright_yellow]")
                if show_thinking:
                    console.print("[dim]Model reasoning will be shown during responses.[/dim]")
                continue

            if user_input.lower() == "/clear":
                # Reset memory to clear context
                if agent.memory:
                    agent.memory.reset()
                    console.print("[bright_green]✓ Conversation memory cleared[/bright_green]")
                    console.print("[dim]Context reset - start fresh![/dim]")
                else:
                    console.print("[dim]No memory to clear[/dim]")
                if show_thinking:
                    console.print(
                        "[dim]Note: Only reasoning models (deepseek-r1, qwq, etc.) show thinking output[/dim]"
                    )
                continue

            if user_input.lower().startswith("/mode"):
                parts = user_input.split()
                if len(parts) == 1:
                    # Show current mode and options
                    console.print(f"\n[bold]Current mode:[/bold] {agent.tool_mode}")
                    console.print("\n[bold]Available modes:[/bold]")
                    for mode_name, mode_desc in TOOL_MODES.items():
                        marker = "→" if mode_name == agent.tool_mode else " "
                        console.print(
                            f"  {marker} [bright_cyan]{mode_name}[/bright_cyan]: {mode_desc}"
                        )
                    console.print("\n[dim]Usage: /mode <name>[/dim]")
                else:
                    new_mode = parts[1].lower()
                    try:
                        console.print(f"[bright_cyan]Switching to {new_mode} mode...[/bright_cyan]")
                        num_tools = agent.set_mode(new_mode)
                        console.print(
                            f"[bright_green]✓ Switched to {new_mode} ({num_tools} tools)[/bright_green]"
                        )
                    except ValueError as e:
                        console.print(f"[bright_red]✗ {e}[/bright_red]")
                continue

            # /file command - read local file and include in message
            if user_input.lower().startswith("/file"):
                # Handle /file without path
                if user_input.lower() == "/file" or user_input[5:].strip() == "":
                    console.print("[bright_yellow]Usage: /file <path>[/bright_yellow]")
                    console.print("[dim]Example: /file examples/mnist_train.py[/dim]")
                    console.print("[dim]         /file ~/scripts/train.py[/dim]")
                    continue

                file_path = user_input[5:].strip()
                # Remove leading space if present
                if file_path.startswith(" "):
                    file_path = file_path[1:]

                try:
                    from pathlib import Path

                    path = Path(file_path).expanduser()
                    if not path.exists():
                        console.print(f"[bright_red]✗ File not found: {file_path}[/bright_red]")
                        console.print("[dim]Check the path and try again[/dim]")
                        continue

                    if not path.is_file():
                        console.print(f"[bright_red]✗ Not a file: {file_path}[/bright_red]")
                        continue

                    content = path.read_text()
                    lines = len(content.splitlines())
                    console.print(
                        f"[bright_green]✓ Read {path.name} ({lines} lines)[/bright_green]"
                    )

                    # Detect file type for syntax highlighting
                    ext = path.suffix.lower()
                    lang = {
                        "py": "python",
                        "js": "javascript",
                        "ts": "typescript",
                        "yaml": "yaml",
                        "yml": "yaml",
                        "json": "json",
                    }.get(ext.lstrip("."), "")

                    # Include file content in next message
                    user_input = f"Here is the contents of `{path.name}`:\n\n```{lang}\n{content}\n```\n\nPlease analyze this file and tell me what it does."
                    # Fall through to normal processing
                except Exception as e:
                    console.print(f"[bright_red]Error reading file: {e}[/bright_red]")
                    continue

            # Show user message
            console.print()
            console.print(
                Panel(
                    Text(user_input, style="white"),
                    title="[bold bright_blue]You[/bold bright_blue]",
                    border_style="bright_blue",
                    padding=(0, 1),
                )
            )

            # Processing indicator
            console.print("[bright_cyan]⏳ Thinking...[/bright_cyan]", end="\r")
            thinking_buffer.clear()
            first_output = [True]

            def on_thinking(delta):
                if show_thinking and delta:  # noqa: B023
                    if first_output[0]:  # noqa: B023
                        console.print(" " * 20, end="\r")  # Clear status
                        first_output[0] = False  # noqa: B023
                    thinking_buffer.append(delta)
                    console.print(
                        f"[bright_magenta italic]{delta}[/bright_magenta italic]",
                        end="",
                        highlight=False,
                    )

            def on_tool_call(tool_info):
                if first_output[0]:  # noqa: B023
                    console.print(" " * 20, end="\r")  # Clear "Thinking..."
                    first_output[0] = False  # noqa: B023
                if thinking_buffer:
                    console.print()  # Newline after thinking
                    thinking_buffer.clear()
                console.print()

                tool_name = tool_info.get("name", "unknown")
                tool_args = tool_info.get("args") or {}

                # Always show tool name
                console.print(f"  [bright_yellow]🔧 {tool_name}[/bright_yellow]")

                # Show arguments
                if tool_args:
                    args_str = json.dumps(tool_args, indent=2, default=str)
                    for line in args_str.split("\n"):
                        console.print(f"     [bright_white]{line}[/bright_white]")
                else:
                    console.print("     [dim](no arguments)[/dim]")

                console.print("[bright_cyan]  ⏳ Executing...[/bright_cyan]", end="\r")

            def on_tool_result(result_info):
                console.print(" " * 30, end="\r")  # Clear "Executing..."
                if result_info.get("result"):
                    result_str = _format_tool_result(result_info["result"])
                    console.print(
                        Panel(
                            Text(result_str, style="white"),
                            title="[bright_green]Result[/bright_green]",
                            border_style="green",
                            padding=(0, 1),
                        )
                    )

            try:
                response, _ = agent.chat(
                    user_input,
                    on_thinking=on_thinking if show_thinking else None,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result,
                )
            except Exception as e:
                console.print()
                error_msg = str(e)
                console.print(
                    Panel(
                        Text(f"{type(e).__name__}: {error_msg}", style="bright_red"),
                        title="[bright_red bold]❌ Error[/bright_red bold]",
                        border_style="red",
                        padding=(0, 1),
                    )
                )
                # Show helpful hints based on error type
                if "does not support tools" in error_msg:
                    console.print(
                        "[yellow]💡 This model doesn't support function calling.[/yellow]"
                    )
                    console.print(
                        "[yellow]   Try: qwen2.5:7b, llama3.2, or mistral (with tools, no thinking)[/yellow]"
                    )
                    console.print("[yellow]   Or: qwq:32b (has both thinking AND tools)[/yellow]")
                elif "connection" in error_msg.lower():
                    console.print("[yellow]💡 Check if Ollama is running: ollama serve[/yellow]")
                elif "timeout" in error_msg.lower():
                    console.print("[yellow]💡 Request timed out. Try a simpler query.[/yellow]")
                continue

            # Clear any pending status
            console.print(" " * 40, end="\r")

            # Notify user if thinking is available (but don't auto-enable - keeps output clean)
            if agent._thinking_supported is True and not hasattr(agent, "_thinking_notified"):
                agent._thinking_notified = True  # type: ignore[attr-defined]
                console.print(
                    "[dim]💭 Thinking supported. Use /think to see model reasoning.[/dim]"
                )

            # Newline after thinking
            if thinking_buffer:
                console.print()

            # Only show assistant panel if there's actual response content
            if response and response.strip():
                console.print()
                console.print(
                    Panel(
                        Markdown(response),
                        title="[bold bright_green]Assistant[/bold bright_green]",
                        border_style="bright_green",
                        padding=(0, 2),
                    )
                )

        except KeyboardInterrupt:
            console.print(
                "\n[yellow]Interrupted. Press Ctrl+C again to quit, or continue typing.[/yellow]"
            )
            try:
                # Wait briefly for another Ctrl+C
                import time

                time.sleep(0.5)
            except KeyboardInterrupt:
                agent.close()
                console.print("[dim italic]Goodbye![/dim italic]")
                break
            continue
        except EOFError:
            agent.close()
            console.print("\n[dim italic]Goodbye![/dim italic]")
            break


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Kubeflow MCP Ollama Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tool modes:
  full        All tools via MCP protocol (~900 tokens) - default, best accuracy
  progressive 3 meta-tools (~85 tokens) - hierarchical discovery, -91% tokens
  semantic    2 meta-tools (~69 tokens) - embedding search, -92% tokens

Examples:
  # Default - all tools via MCP protocol
  python -m kubeflow_mcp.agents.ollama

  # Progressive mode (minimal tokens, hierarchical discovery)
  python -m kubeflow_mcp.agents.ollama --mode progressive

  # Semantic mode (requires: pip install sentence-transformers)
  python -m kubeflow_mcp.agents.ollama --mode semantic
        """,
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model")
    parser.add_argument("--url", default=DEFAULT_URL, help="Ollama server URL")
    parser.add_argument(
        "--mode",
        choices=["full", "progressive", "semantic", "static", "mcp"],  # static/mcp are legacy aliases
        default="full",
        help="Tool loading mode: full (all tools), progressive (hierarchical), semantic (embedding search)",
    )
    args = parser.parse_args()

    run_chat(model=args.model, url=args.url, tool_mode=args.mode)


if __name__ == "__main__":
    main()

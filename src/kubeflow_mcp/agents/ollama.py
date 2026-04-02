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

from kubeflow_mcp.trainer import TOOLS  # noqa: E402

console = Console()

DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_URL = "http://localhost:11434"

SYSTEM_PROMPT = """You are a Kubeflow training assistant.

Available actions:
- Check cluster resources and GPUs
- Estimate resources for models
- Submit and manage training jobs
- View logs and job status

Rules:
- Only call tools when user requests an action
- For greetings or questions, respond naturally
- Always use confirmed=False first to preview, then confirmed=True after user approval
"""


def create_tools() -> list[FunctionTool]:
    """Convert kubeflow-mcp tools to LlamaIndex FunctionTools."""
    tools = []
    for tool_func in TOOLS:
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
    """Ollama agent using LlamaIndex FunctionAgent with thinking support."""

    _agent: FunctionAgent | None
    _tools: list[FunctionTool] | None
    _thinking_supported: bool | None
    memory: ChatMemoryBuffer | None
    llm: Ollama | None

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_URL):
        self.model = model
        self.base_url = base_url
        self._agent = None
        self._tools = None
        self._thinking_supported = None  # None = unknown, True/False = tested
        self._use_thinking = True  # User preference
        self.memory = None
        self.llm = None

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
            self._tools = create_tools()
            self.llm = self._create_llm(with_thinking)
            self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

            self._agent = FunctionAgent(
                tools=self._tools,  # type: ignore[arg-type]
                llm=self.llm,
                memory=self.memory,
                system_prompt=SYSTEM_PROMPT,
            )
        finally:
            sys.stderr = old_stderr

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
                    system_prompt=SYSTEM_PROMPT,
                )
            finally:
                sys.stderr = old_stderr

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
                    # Stream thinking output
                    if event.thinking_delta and on_thinking:
                        on_thinking(event.thinking_delta)

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
        """Synchronous chat wrapper using dedicated event loop."""
        import asyncio

        future = asyncio.run_coroutine_threadsafe(
            self._chat_async(message, on_thinking, on_tool_call, on_tool_result),
            self._loop,
        )
        return future.result(timeout=300)  # 5 min timeout

    def close(self):
        """Clean up agent resources."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop_thread.join(timeout=5)


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


def run_chat(model: str = DEFAULT_MODEL, url: str = DEFAULT_URL):
    """Run interactive chat loop with rich UI."""
    # Welcome panel
    welcome = Table.grid(padding=(0, 1))
    welcome.add_column(justify="left")
    welcome.add_row(Text("Kubeflow Training Assistant", style="bold bright_cyan"))
    welcome.add_row(Text(f"Model: {model}", style="bright_green"))
    welcome.add_row(Text(f"Ollama: {url}", style="bright_white"))
    welcome.add_row()
    welcome.add_row(Text("Commands:", style="bright_yellow"))
    welcome.add_row(Text("  /tools  - List available tools", style="white"))
    welcome.add_row(Text("  /think  - Toggle thinking mode (for reasoning models)", style="white"))
    welcome.add_row(Text("  exit    - Quit the agent", style="white"))
    welcome.add_row(Text("  Ctrl+C  - Cancel current request", style="white"))

    # Check model capabilities
    # Models with BOTH thinking AND tool support
    thinking_with_tools = ["qwq", "phi4-reasoning", "phi4-mini-reasoning", "qwen3"]
    # Models with thinking but NO tool support
    thinking_no_tools = ["deepseek-r1", "lfm2.5-thinking", "marco-o1"]

    has_thinking_and_tools = any(tm in model.lower() for tm in thinking_with_tools)
    has_thinking_no_tools = any(tm in model.lower() for tm in thinking_no_tools)

    if has_thinking_and_tools:
        welcome.add_row()
        welcome.add_row(Text("💭 Thinking + Tools supported!", style="bright_magenta"))
    elif has_thinking_no_tools:
        welcome.add_row()
        welcome.add_row(
            Text("⚠️  This model has thinking but NO tool support", style="bright_yellow")
        )
        welcome.add_row(Text("   Try: phi4-mini-reasoning or qwen3:8b", style="yellow"))

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

    agent = OllamaAgent(model=model, base_url=url)

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

    # State
    show_thinking = True
    thinking_buffer: list[str] = []

    while True:
        try:
            console.print()
            user_input = console.input("[bold bright_blue]You →[/bold bright_blue] ").strip()

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
                    console.print(
                        "[dim]Note: Only reasoning models (deepseek-r1, qwq, etc.) show thinking output[/dim]"
                    )
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

            # Newline after thinking
            if thinking_buffer:
                console.print()

            # Assistant response
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
            console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            continue
        except EOFError:
            agent.close()
            console.print("\n[dim italic]Goodbye![/dim italic]")
            break


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Kubeflow MCP Ollama Agent")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model")
    parser.add_argument("--url", default=DEFAULT_URL, help="Ollama server URL")
    args = parser.parse_args()

    run_chat(model=args.model, url=args.url)


if __name__ == "__main__":
    main()

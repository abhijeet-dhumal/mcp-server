"""Kubeflow MCP Server CLI."""

import click

from kubeflow_mcp import __version__


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Kubeflow MCP Server - AI interface for Kubeflow Training."""
    pass


@cli.command()
@click.option(
    "--clients",
    "-c",
    default="trainer",
    help="Comma-separated client modules (trainer, optimizer, hub)",
)
@click.option(
    "--persona",
    "-p",
    default="ml-engineer",
    type=click.Choice(["readonly", "data-scientist", "ml-engineer", "platform-admin"]),
    help="Persona for tool filtering",
)
@click.option(
    "--transport",
    "-t",
    default="stdio",
    type=click.Choice(["stdio", "http"]),
    help="MCP transport protocol",
)
@click.option(
    "--log-level",
    "-l",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Logging level",
)
@click.option(
    "--log-format",
    default=None,
    type=click.Choice(["json", "console"]),
    help="Log format (auto-detects if not specified)",
)
def serve(
    clients: str,
    persona: str,
    transport: str,
    log_level: str,
    log_format: str | None,
) -> None:
    """Start the MCP server."""
    from kubeflow_mcp.core.logging import setup_logging
    from kubeflow_mcp.core.server import create_server

    logger = setup_logging(level=log_level, format=log_format)
    logger.info(
        "Starting kubeflow-mcp",
        extra={"clients": clients, "persona": persona, "transport": transport},
    )

    client_list = [c.strip() for c in clients.split(",")]
    server = create_server(clients=client_list, persona=persona)

    if transport == "stdio":
        server.run()
    else:
        server.run(transport="streamable-http")


@cli.command()
def status() -> None:
    """Show server status and enabled tools."""
    from kubeflow_mcp.core.server import CLIENT_MODULES

    click.echo("Kubeflow MCP Server Status")
    click.echo("-" * 40)
    click.echo(f"Version: {__version__}")
    click.echo("\nAvailable clients:")
    for name, module_path in CLIENT_MODULES.items():
        try:
            import importlib

            module = importlib.import_module(module_path)
            info = getattr(module, "MODULE_INFO", {})
            status = info.get("status", "unknown")
            tools = len(getattr(module, "TOOLS", []))
            click.echo(f"  {name}: {status} ({tools} tools)")
        except ImportError:
            click.echo(f"  {name}: not installed")


if __name__ == "__main__":
    cli()

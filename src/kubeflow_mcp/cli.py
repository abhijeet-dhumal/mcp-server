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
    multiple=True,
    default=["trainer"],
    help="Kubeflow clients to enable (trainer, optimizer, hub)",
)
@click.option("--log-level", default="INFO", help="Logging level")
@click.option("--log-format", default="console", help="Log format (console, json)")
def serve(clients: tuple[str, ...], log_level: str, log_format: str) -> None:
    """Start the MCP server."""
    click.echo(f"Starting Kubeflow MCP Server v{__version__}")
    click.echo(f"Enabled clients: {', '.join(clients)}")
    click.echo(f"Log level: {log_level}, format: {log_format}")
    click.echo("Server not yet implemented - Stage 1 required")


@cli.command()
def status() -> None:
    """Show server status and enabled tools."""
    click.echo("Kubeflow MCP Server Status")
    click.echo("-" * 30)
    click.echo("Status: Not running")
    click.echo("Tools: 0 registered")
    click.echo("Skills: 0 loaded")


if __name__ == "__main__":
    cli()

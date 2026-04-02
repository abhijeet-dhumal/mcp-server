"""Test CLI commands."""

from click.testing import CliRunner

from kubeflow_mcp.cli import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0-dev" in result.output


def test_serve_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--clients", "trainer"])
    assert result.exit_code == 0
    assert "trainer" in result.output


def test_status_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Status" in result.output

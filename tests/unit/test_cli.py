"""Test CLI commands."""

from click.testing import CliRunner

from kubeflow_mcp.cli import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0-dev" in result.output


def test_status_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "trainer" in result.output
    assert "implemented" in result.output


def test_status_shows_stubs():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert "optimizer" in result.output
    assert "stub" in result.output

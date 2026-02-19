"""Integration tests — verify the tool installs and runs."""

from click.testing import CliRunner

from ai_cli.cli import main


def test_help_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Generate a bash command" in result.output


def test_no_args_shows_help():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert "Generate a bash command" in result.output

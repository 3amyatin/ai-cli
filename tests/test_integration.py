"""Integration tests — verify the tool installs and runs."""

from unittest.mock import patch

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


def test_double_dash_separates_options_from_task():
    """Everything after -- is treated as task text."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="echo hi") as mock_llm,
    ):
        runner.invoke(main, ["--", "-v", "list", "files"], input="n\n")

    # "-v" should be part of the task, not parsed as a flag
    call_args = mock_llm.call_args
    task_sent = call_args.args[0] if call_args.args else call_args.kwargs.get("task", "")
    assert "-v" in task_sent


def test_help_shows_all_options():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "-v" in result.output
    assert "-m" in result.output
    assert "-M" in result.output


def test_verbose_flag_in_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "explanation" in result.output.lower() or "verbose" in result.output.lower()

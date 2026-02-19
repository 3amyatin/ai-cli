from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from ai_cli import __version__
from ai_cli.cli import main


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_verbose_flag_shows_model_and_prompt():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="ls -la"),
    ):
        result = runner.invoke(main, ["-v", "list", "files"], input="n\n")

    assert result.exit_code == 0
    assert "Model:" in result.output
    assert "System:" in result.output


def test_verbose_long_flag():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="ls -la"),
    ):
        result = runner.invoke(main, ["--verbose", "list", "files"], input="n\n")

    assert result.exit_code == 0
    assert "Model:" in result.output


def test_generates_and_displays_command():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="ls -la /tmp"),
    ):
        result = runner.invoke(main, ["list", "files", "in", "tmp"], input="n\n")

    assert result.exit_code == 0
    assert "ls -la /tmp" in result.output


def test_executes_on_confirmation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="echo hello"),
        patch("ai_cli.cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["say", "hello"], input="y\n")

    assert result.exit_code == 0
    mock_run.assert_called_once()


def test_aborts_on_decline():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="rm -rf /"),
    ):
        result = runner.invoke(main, ["delete", "everything"], input="n\n")

    assert result.exit_code == 0
    assert "Aborted" in result.output or "abort" in result.output.lower()


def test_handles_empty_llm_response():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=None),
    ):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "no command" in result.output.lower() or "error" in result.output.lower()


def test_execute_default_is_yes():
    """Pressing Enter without input should execute the command."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="echo test"),
        patch("ai_cli.cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["test"], input="\n")

    assert result.exit_code == 0
    mock_run.assert_called_once()


def test_handles_ollama_connection_error():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", side_effect=Exception("Connection refused")),
    ):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "error" in result.output.lower()


def test_verbose_flag_shows_explanation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=("ls -lS", "Lists files by size")),
    ):
        result = runner.invoke(main, ["-v", "list", "files"], input="n\n")

    assert "Lists files by size" in result.output
    assert "ls -lS" in result.output


def test_verbose_flag_no_explanation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=("ls -lS", None)),
    ):
        result = runner.invoke(main, ["-v", "list", "files"], input="n\n")

    assert "ls -lS" in result.output


def test_verbose_flag_none_response():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=None),
    ):
        result = runner.invoke(main, ["-v", "list", "files"])

    assert result.exit_code == 1
    assert "no command" in result.output.lower() or "error" in result.output.lower()

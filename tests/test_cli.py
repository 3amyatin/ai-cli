from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from ai_cli.cli import main


def test_generates_and_displays_command():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", return_value="ls -la /tmp"):
        result = runner.invoke(main, ["list", "files", "in", "tmp"], input="n\n")

    assert result.exit_code == 0
    assert "ls -la /tmp" in result.output


def test_executes_on_confirmation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ask_llm", return_value="echo hello"),
        patch("ai_cli.cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["say", "hello"], input="y\n")

    assert result.exit_code == 0
    mock_run.assert_called_once()


def test_aborts_on_decline():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", return_value="rm -rf /"):
        result = runner.invoke(main, ["delete", "everything"], input="n\n")

    assert result.exit_code == 0
    assert "Aborted" in result.output or "abort" in result.output.lower()


def test_handles_empty_llm_response():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", return_value=None):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "no command" in result.output.lower() or "error" in result.output.lower()


def test_handles_ollama_connection_error():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", side_effect=Exception("Connection refused")):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "error" in result.output.lower()

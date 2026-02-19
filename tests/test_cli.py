import os
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from ai_cli import __version__
from ai_cli.cli import main
from ai_cli.llm import LLMResponse


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_verbose_long_flag():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="ls -la")),
    ):
        result = runner.invoke(main, ["--verbose", "list", "files"], input="n\n")

    assert result.exit_code == 0
    assert "ls -la" in result.output


def test_generates_and_displays_command():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="ls -la /tmp")),
    ):
        result = runner.invoke(main, ["list", "files", "in", "tmp"], input="n\n")

    assert result.exit_code == 0
    assert "ls -la /tmp" in result.output


def test_executes_on_confirmation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hello")),
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
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="rm -rf /")),
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
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo test")),
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
        patch(
            "ai_cli.cli.ask_llm",
            return_value=LLMResponse(command="ls -lS", explanation="Lists files by size"),
        ),
    ):
        result = runner.invoke(main, ["-v", "list", "files"], input="n\n")

    assert "Lists files by size" in result.output
    assert "ls -lS" in result.output


def test_verbose_flag_no_explanation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="ls -lS")),
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


def test_m_flag_with_value_uses_specified_model():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
    ):
        result = runner.invoke(main, ["-m", "llama3", "say", "hi"], input="n\n")

    assert result.exit_code == 0
    mock_llm.assert_called_once()
    assert mock_llm.call_args.kwargs.get("model") == "llama3"


def test_interactive_flag_picks_and_saves_model():
    """--interactive invokes _pick_model and saves the choice."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli._pick_model", return_value="qwen2.5:7b") as mock_pick,
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
        patch("ai_cli.cli.save_config") as mock_save,
    ):
        result = runner.invoke(main, ["--interactive", "say", "hi"], input="n\n")

    assert result.exit_code == 0
    mock_pick.assert_called_once()
    assert mock_llm.call_args.kwargs.get("model") == "qwen2.5:7b"
    mock_save.assert_called_once_with({"model": "qwen2.5:7b"})


def test_pick_model_connection_error():
    """_pick_model exits gracefully when ollama is not reachable."""
    from ai_cli.cli import _pick_model

    with patch("ai_cli.cli.ollama_list", side_effect=ConnectionError("refused")):
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            _pick_model()

    assert exc_info.value.code == 1


def test_pick_model_lists_and_selects():
    """_pick_model lists installed models and returns the selected one."""
    from ai_cli.cli import _pick_model

    mock_resp = MagicMock()
    model_a = MagicMock()
    model_a.model = "qwen2.5:7b"
    model_a.size = 4_000_000_000
    model_b = MagicMock()
    model_b.model = "llama3:latest"
    model_b.size = 5_000_000_000
    mock_resp.models = [model_a, model_b]

    with (
        patch("ai_cli.cli.ollama_list", return_value=mock_resp),
        patch("click.prompt", return_value=2),
    ):
        result = _pick_model()

    assert result == "llama3:latest"


def test_big_m_flag_saves_model_after_ensure_ready():
    """Model is saved to config only after ensure_ready succeeds."""
    runner = CliRunner()
    call_order = []

    def track_ensure_ready(model):
        call_order.append("ensure_ready")

    def track_save_config(data):
        call_order.append("save_config")

    with (
        patch("ai_cli.cli.ensure_ready", side_effect=track_ensure_ready),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")),
        patch("ai_cli.cli.save_config", side_effect=track_save_config),
    ):
        result = runner.invoke(main, ["-M", "llama3", "say", "hi"], input="n\n")

    assert result.exit_code == 0
    assert call_order == ["ensure_ready", "save_config"]


def test_big_m_flag_does_not_save_if_ensure_ready_fails():
    """If ensure_ready exits, model is NOT saved to config."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready", side_effect=SystemExit(1)),
        patch("ai_cli.cli.save_config") as mock_save,
    ):
        result = runner.invoke(main, ["-M", "bad-model", "say", "hi"])

    assert result.exit_code == 1
    mock_save.assert_not_called()


def test_config_model_used_when_no_flags(tmp_path):
    """Config file model is used when no -m/-M and no AI_MODEL env."""
    runner = CliRunner()

    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
        patch("ai_cli.cli.load_config", return_value={"model": "mistral:latest"}),
        patch.dict(os.environ, {}, clear=True),
    ):
        runner.invoke(main, ["say", "hi"], input="n\n")

    assert mock_llm.call_args.kwargs.get("model") == "mistral:latest"


def test_env_var_overrides_config():
    """AI_MODEL env var takes priority over config file."""
    runner = CliRunner()

    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
        patch("ai_cli.cli.load_config", return_value={"model": "mistral:latest"}),
        patch.dict(os.environ, {"AI_MODEL": "codellama:7b"}),
    ):
        runner.invoke(main, ["say", "hi"], input="n\n")

    assert mock_llm.call_args.kwargs.get("model") == "codellama:7b"

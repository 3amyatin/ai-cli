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
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="ls -la")),
    ):
        result = runner.invoke(main, ["--verbose", "list", "files"], input="a\n")

    assert result.exit_code == 0
    assert "ls -la" in result.output


def test_generates_and_displays_command():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="ls -la /tmp")),
    ):
        result = runner.invoke(main, ["list", "files", "in", "tmp"], input="a\n")

    assert result.exit_code == 0
    assert "ls -la /tmp" in result.output


def test_executes_on_confirmation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hello")),
        patch("ai_cli.cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["say", "hello"], input="e\n")

    assert result.exit_code == 0
    mock_run.assert_called_once_with("echo hello", shell=True)


def test_aborts_on_decline():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="rm -rf /")),
    ):
        result = runner.invoke(main, ["delete", "everything"], input="a\n")

    assert result.exit_code == 0
    assert "Aborted" in result.output


def test_handles_empty_llm_response():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=None),
    ):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "no command" in result.output.lower() or "error" in result.output.lower()


def test_execute_default_is_execute():
    """Pressing Enter without input should execute the command (default=e)."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo test")),
        patch("ai_cli.cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["test"], input="\n")

    assert result.exit_code == 0
    mock_run.assert_called_once_with("echo test", shell=True)


def test_copy_to_clipboard():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="find . -name '*.py'")),
        patch("ai_cli.cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["find", "python", "files"], input="c\n")

    assert result.exit_code == 0
    assert "Copied" in result.output
    mock_run.assert_called_once_with(["pbcopy"], input=b"find . -name '*.py'", check=True)


def test_history_logged_on_execute(tmp_path):
    import json

    history_path = tmp_path / "history.jsonl"
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")),
        patch("ai_cli.cli.subprocess.run") as mock_run,
        patch("ai_cli.cli.HISTORY_PATH", history_path),
    ):
        mock_run.return_value = MagicMock(returncode=0)
        runner.invoke(main, ["say", "hi"], input="e\n")

    entries = [json.loads(line) for line in history_path.read_text().splitlines()]
    assert len(entries) == 1
    assert entries[0]["task"] == "say hi"
    assert entries[0]["command"] == "echo hi"
    assert entries[0]["action"] == "execute"
    assert "ts" in entries[0]
    assert "model" in entries[0]


def test_history_logged_on_abort(tmp_path):
    import json

    history_path = tmp_path / "history.jsonl"
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="rm -rf /")),
        patch("ai_cli.cli.HISTORY_PATH", history_path),
    ):
        runner.invoke(main, ["delete", "everything"], input="a\n")

    entries = [json.loads(line) for line in history_path.read_text().splitlines()]
    assert len(entries) == 1
    assert entries[0]["action"] == "abort"


def test_handles_ollama_connection_error():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", side_effect=Exception("Connection refused")),
    ):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "error" in result.output.lower()


def test_verbose_flag_shows_explanation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch(
            "ai_cli.cli.ask_llm",
            return_value=LLMResponse(command="ls -lS", explanation="Lists files by size"),
        ),
    ):
        result = runner.invoke(main, ["-v", "list", "files"], input="a\n")

    assert "Lists files by size" in result.output
    assert "ls -lS" in result.output


def test_verbose_flag_no_explanation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="ls -lS")),
    ):
        result = runner.invoke(main, ["-v", "list", "files"], input="a\n")

    assert "ls -lS" in result.output


def test_verbose_flag_none_response():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=None),
    ):
        result = runner.invoke(main, ["-v", "list", "files"])

    assert result.exit_code == 1
    assert "no command" in result.output.lower() or "error" in result.output.lower()


def test_m_flag_with_value_uses_specified_model():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
    ):
        result = runner.invoke(main, ["-m", "llama3", "say", "hi"], input="a\n")

    assert result.exit_code == 0
    mock_llm.assert_called_once()
    assert mock_llm.call_args.kwargs.get("model") == "llama3"


def test_interactive_flag_picks_and_saves_model():
    """--interactive invokes _pick_model and saves the choice."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli._pick_model", return_value="qwen2.5:7b") as mock_pick,
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
        patch("ai_cli.cli.save_config") as mock_save,
    ):
        result = runner.invoke(main, ["--interactive", "say", "hi"], input="a\n")

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
        result = runner.invoke(main, ["-M", "llama3", "say", "hi"], input="a\n")

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
    """When no -m/-M flags, model=None is passed to ask_llm (resolution happens there)."""
    runner = CliRunner()

    with (
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
        patch.dict(os.environ, {}, clear=True),
    ):
        runner.invoke(main, ["say", "hi"], input="a\n")

    assert mock_llm.call_args.kwargs.get("model") is None


def test_interactive_flag_without_task_saves_and_exits():
    """ai -i (no task) picks model, saves it, and exits without error."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli._pick_model", return_value="llama3:latest") as mock_pick,
        patch("ai_cli.cli.save_config") as mock_save,
    ):
        result = runner.invoke(main, ["-i"])

    assert result.exit_code == 0
    mock_pick.assert_called_once()
    mock_save.assert_called_once_with({"model": "llama3:latest"})
    assert "llama3:latest" in result.output


def test_big_m_flag_without_task_saves_and_exits():
    """ai -M model (no task) saves model and exits without error."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_server"),
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.save_config") as mock_save,
    ):
        result = runner.invoke(main, ["-M", "mistral:latest"])

    assert result.exit_code == 0
    mock_save.assert_called_once_with({"model": "mistral:latest"})
    assert "mistral:latest" in result.output


def test_env_var_overrides_config():
    """AI_MODEL env var resolution now happens inside ask_llm, not cli."""
    runner = CliRunner()

    with (
        patch("ai_cli.cli.ask_llm", return_value=LLMResponse(command="echo hi")) as mock_llm,
        patch.dict(os.environ, {"AI_MODEL": "codellama:7b"}),
    ):
        runner.invoke(main, ["say", "hi"], input="a\n")

    # CLI passes model=None; ask_llm internally resolves AI_MODEL
    assert mock_llm.call_args.kwargs.get("model") is None

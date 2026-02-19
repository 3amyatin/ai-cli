"""Tests for ollama setup/readiness checks."""

from unittest.mock import MagicMock, patch

import pytest

from ai_cli.setup import ensure_ready


@pytest.fixture()
def mock_model():
    """Create a mock model object with a .model attribute."""
    m = MagicMock()
    m.model = "qwen2.5:7b"
    return m


@pytest.fixture()
def mock_list_response(mock_model):
    """Create a mock ListResponse with one model."""
    resp = MagicMock()
    resp.models = [mock_model]
    return resp


# --- Connection failure: binary missing ---


@patch("ai_cli.setup.shutil_which", return_value=None)
@patch("ai_cli.setup.ollama_list", side_effect=ConnectionError("connection refused"))
def test_connection_error_binary_missing_prints_install_instructions(
    _mock_list, _mock_which, capsys
):
    with pytest.raises(SystemExit) as exc_info:
        ensure_ready("qwen2.5:7b")

    assert exc_info.value.code == 1
    output = capsys.readouterr().err
    assert "install" in output.lower()
    assert "ollama" in output.lower()


@patch("ai_cli.setup.shutil_which", return_value=None)
@patch("ai_cli.setup.ollama_list", side_effect=ConnectionError("connection refused"))
def test_connection_error_binary_missing_exits_with_1(_mock_list, _mock_which):
    with pytest.raises(SystemExit) as exc_info:
        ensure_ready("qwen2.5:7b")

    assert exc_info.value.code == 1


# --- Connection failure: binary exists but server not running ---


@patch("ai_cli.setup.shutil_which", return_value="/usr/local/bin/ollama")
@patch("ai_cli.setup.ollama_list", side_effect=ConnectionError("connection refused"))
def test_connection_error_binary_exists_prints_serve_suggestion(
    _mock_list, _mock_which, capsys
):
    with pytest.raises(SystemExit) as exc_info:
        ensure_ready("qwen2.5:7b")

    assert exc_info.value.code == 1
    output = capsys.readouterr().err
    assert "ollama serve" in output


@patch("ai_cli.setup.shutil_which", return_value="/usr/local/bin/ollama")
@patch("ai_cli.setup.ollama_list", side_effect=ConnectionError("connection refused"))
def test_connection_error_binary_exists_exits_with_1(_mock_list, _mock_which):
    with pytest.raises(SystemExit) as exc_info:
        ensure_ready("qwen2.5:7b")

    assert exc_info.value.code == 1


# --- Connected, model already present ---


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_already_present_does_not_pull(mock_list, mock_pull, mock_list_response):
    mock_list.return_value = mock_list_response

    ensure_ready("qwen2.5:7b")

    mock_pull.assert_not_called()


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_present_no_output(mock_list, mock_pull, mock_list_response, capsys):
    mock_list.return_value = mock_list_response

    ensure_ready("qwen2.5:7b")

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


# --- Connected, model missing → auto-pull ---


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_missing_triggers_pull(mock_list, mock_pull):
    resp = MagicMock()
    resp.models = []  # no models
    mock_list.return_value = resp

    progress1 = MagicMock()
    progress1.status = "downloading"
    progress1.completed = 50
    progress1.total = 100

    progress2 = MagicMock()
    progress2.status = "success"
    progress2.completed = 100
    progress2.total = 100

    mock_pull.return_value = iter([progress1, progress2])

    ensure_ready("llama3")

    mock_pull.assert_called_once_with("llama3", stream=True)


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_missing_prints_pulling_message(mock_list, mock_pull, capsys):
    resp = MagicMock()
    resp.models = []
    mock_list.return_value = resp

    progress = MagicMock()
    progress.status = "success"
    progress.completed = None
    progress.total = None
    mock_pull.return_value = iter([progress])

    ensure_ready("llama3")

    output = capsys.readouterr().err
    assert "llama3" in output
    assert "pulling" in output.lower() or "pull" in output.lower()


# --- Model name matching edge cases ---


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_name_exact_match(mock_list, mock_pull):
    """Model name must match exactly."""
    model_a = MagicMock()
    model_a.model = "qwen2.5:7b"
    model_b = MagicMock()
    model_b.model = "llama3:latest"

    resp = MagicMock()
    resp.models = [model_a, model_b]
    mock_list.return_value = resp

    ensure_ready("llama3:latest")

    mock_pull.assert_not_called()


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_not_in_list_triggers_pull(mock_list, mock_pull):
    """If model name doesn't match any installed model, pull is triggered."""
    model_a = MagicMock()
    model_a.model = "qwen2.5:7b"

    resp = MagicMock()
    resp.models = [model_a]
    mock_list.return_value = resp

    progress = MagicMock()
    progress.status = "success"
    progress.completed = None
    progress.total = None
    mock_pull.return_value = iter([progress])

    ensure_ready("llama3:latest")

    mock_pull.assert_called_once_with("llama3:latest", stream=True)


# --- Pull progress output ---


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_pull_progress_with_bytes_shows_progress(mock_list, mock_pull, capsys):
    """When pull reports completed/total bytes, progress is displayed."""
    resp = MagicMock()
    resp.models = []
    mock_list.return_value = resp

    progress = MagicMock()
    progress.status = "downloading"
    progress.completed = 500_000_000
    progress.total = 1_000_000_000

    mock_pull.return_value = iter([progress])

    ensure_ready("llama3")

    output = capsys.readouterr().err
    assert "50%" in output


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_pull_progress_without_bytes_shows_status(mock_list, mock_pull, capsys):
    """When pull reports only status (no bytes), status text is displayed."""
    resp = MagicMock()
    resp.models = []
    mock_list.return_value = resp

    progress = MagicMock()
    progress.status = "verifying sha256 digest"
    progress.completed = None
    progress.total = None

    mock_pull.return_value = iter([progress])

    ensure_ready("llama3")

    output = capsys.readouterr().err
    assert "verifying" in output.lower()


# --- Pull failure ---


@patch("ai_cli.setup.ollama_pull", side_effect=Exception("network timeout"))
@patch("ai_cli.setup.ollama_list")
def test_pull_failure_prints_error_and_exits(mock_list, _mock_pull, capsys):
    """If ollama_pull raises an exception, print a friendly error and exit(1)."""
    resp = MagicMock()
    resp.models = []
    mock_list.return_value = resp

    with pytest.raises(SystemExit) as exc_info:
        ensure_ready("llama3")

    assert exc_info.value.code == 1
    output = capsys.readouterr().err
    assert "failed to pull" in output.lower()
    assert "llama3" in output
    assert "network timeout" in output

"""Tests for LLM integration."""

from unittest.mock import MagicMock, patch

from ai_cli.llm import _detect_env, ask_llm


def test_detect_env_returns_os_arch_shell():
    env = _detect_env()
    assert "os" in env
    assert "arch" in env
    assert "shell" in env
    assert env["os"]  # non-empty
    assert env["shell"]  # non-empty


def test_detect_env_reads_shell_from_env():
    with patch.dict("os.environ", {"SHELL": "/opt/homebrew/bin/fish"}):
        env = _detect_env()
    assert env["shell"] == "fish"


def test_ask_llm_returns_command():
    mock_response = MagicMock()
    mock_response.message.content = "ls -la /tmp"

    with patch("ai_cli.llm.chat", return_value=mock_response) as mock_chat:
        result = ask_llm("list files in tmp")

    assert result == "ls -la /tmp"
    mock_chat.assert_called_once()
    call_kwargs = mock_chat.call_args
    assert call_kwargs.kwargs["model"] == "qwen2.5:7b"
    messages = call_kwargs.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "list files in tmp"


def test_ask_llm_system_prompt_includes_env():
    mock_response = MagicMock()
    mock_response.message.content = "echo hi"

    with patch("ai_cli.llm.chat", return_value=mock_response) as mock_chat:
        ask_llm("say hi")

    system_msg = mock_chat.call_args.kwargs["messages"][0]["content"]
    env = _detect_env()
    assert env["os"] in system_msg
    assert env["shell"] in system_msg


def test_ask_llm_strips_markdown_backticks():
    mock_response = MagicMock()
    mock_response.message.content = "```bash\nls -la\n```"

    with patch("ai_cli.llm.chat", return_value=mock_response):
        result = ask_llm("list files")

    assert result == "ls -la"


def test_ask_llm_custom_model():
    mock_response = MagicMock()
    mock_response.message.content = "echo hello"

    with patch("ai_cli.llm.chat", return_value=mock_response) as mock_chat:
        result = ask_llm("say hello", model="llama3")

    assert mock_chat.call_args.kwargs["model"] == "llama3"
    assert result == "echo hello"


def test_ask_llm_empty_response():
    mock_response = MagicMock()
    mock_response.message.content = ""

    with patch("ai_cli.llm.chat", return_value=mock_response):
        result = ask_llm("do something")

    assert result is None

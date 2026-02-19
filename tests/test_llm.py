"""Tests for LLM integration."""

from unittest.mock import MagicMock, patch

from ai_cli.llm import LLMResponse, _detect_env, _parse_verbose_response, ask_llm


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

    assert result == LLMResponse(command="ls -la /tmp")
    assert result.command == "ls -la /tmp"
    assert result.explanation is None
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

    assert result.command == "ls -la"


def test_ask_llm_custom_model():
    mock_response = MagicMock()
    mock_response.message.content = "echo hello"

    with patch("ai_cli.llm.chat", return_value=mock_response) as mock_chat:
        result = ask_llm("say hello", model="llama3")

    assert mock_chat.call_args.kwargs["model"] == "llama3"
    assert result.command == "echo hello"


def test_ask_llm_empty_response():
    mock_response = MagicMock()
    mock_response.message.content = ""

    with patch("ai_cli.llm.chat", return_value=mock_response):
        result = ask_llm("do something")

    assert result is None


def test_parse_verbose_response_with_markers():
    result = _parse_verbose_response(
        "EXPLANATION: Lists files sorted by size\nCOMMAND: ls -lS /tmp"
    )
    assert result == LLMResponse(command="ls -lS /tmp", explanation="Lists files sorted by size")


def test_parse_verbose_response_without_markers():
    result = _parse_verbose_response("ls -lS /tmp")
    assert result.command == "ls -lS /tmp"
    assert result.explanation is None


def test_parse_verbose_response_strips_markdown():
    result = _parse_verbose_response("```bash\nls -la\n```")
    assert result.command == "ls -la"
    assert result.explanation is None


def test_parse_verbose_response_multiline_explanation():
    result = _parse_verbose_response(
        "EXPLANATION: This lists files\nsorted by size in reverse order\nCOMMAND: ls -lSr /tmp"
    )
    assert result.command == "ls -lSr /tmp"
    assert "lists files" in result.explanation
    assert "sorted by size" in result.explanation


def test_ask_llm_verbose_returns_explanation_and_command():
    mock_response = MagicMock()
    mock_response.message.content = (
        "EXPLANATION: Lists files sorted by size\nCOMMAND: ls -lS /tmp"
    )

    with patch("ai_cli.llm.chat", return_value=mock_response):
        result = ask_llm("list files by size", verbose=True)

    assert result == LLMResponse(command="ls -lS /tmp", explanation="Lists files sorted by size")


def test_ask_llm_verbose_fallback_when_no_markers():
    """If LLM doesn't follow format, treat whole response as command."""
    mock_response = MagicMock()
    mock_response.message.content = "ls -lS /tmp"

    with patch("ai_cli.llm.chat", return_value=mock_response):
        result = ask_llm("list files by size", verbose=True)

    assert result == LLMResponse(command="ls -lS /tmp")


def test_ask_llm_verbose_uses_different_system_prompt():
    mock_response = MagicMock()
    mock_response.message.content = "EXPLANATION: test\nCOMMAND: echo hi"

    with patch("ai_cli.llm.chat", return_value=mock_response) as mock_chat:
        ask_llm("say hi", verbose=True)

    system_msg = mock_chat.call_args.kwargs["messages"][0]["content"]
    assert "EXPLANATION" in system_msg
    assert "COMMAND" in system_msg

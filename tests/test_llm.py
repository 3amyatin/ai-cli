"""Tests for LLM integration."""

from unittest.mock import MagicMock, patch

from ai_cli.llm import LLMResponse, _detect_env, _parse_verbose_response, _resolve_model, ask_llm


def _mock_client(content: str):
    """Create a mock Client whose chat() returns given content."""
    mock_response = MagicMock()
    mock_response.message.content = content
    mock_client_instance = MagicMock()
    mock_client_instance.chat.return_value = mock_response
    return mock_client_instance


def test_detect_env_returns_os_arch_shell():
    env = _detect_env()
    assert "os" in env
    assert "arch" in env
    assert "shell" in env
    assert "env_context" in env
    assert env["os"]  # non-empty
    assert env["shell"]  # non-empty
    assert "Working directory" in env["env_context"]
    assert "Home" in env["env_context"]


def test_detect_env_reads_shell_from_env():
    with patch.dict("os.environ", {"SHELL": "/opt/homebrew/bin/fish"}):
        env = _detect_env()
    assert env["shell"] == "fish"


def test_ask_llm_returns_command():
    client = _mock_client("ls -la /tmp")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        result = ask_llm("list files in tmp")

    assert result == LLMResponse(command="ls -la /tmp")
    assert result.command == "ls -la /tmp"
    assert result.explanation is None
    client.chat.assert_called_once()
    call_kwargs = client.chat.call_args
    assert call_kwargs.kwargs["model"] == "glm-5:cloud"
    messages = call_kwargs.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "list files in tmp"


def test_ask_llm_system_prompt_includes_env():
    client = _mock_client("echo hi")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        ask_llm("say hi")

    system_msg = client.chat.call_args.kwargs["messages"][0]["content"]
    env = _detect_env()
    assert env["os"] in system_msg
    assert env["shell"] in system_msg


def test_ask_llm_strips_markdown_backticks():
    client = _mock_client("```bash\nls -la\n```")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        result = ask_llm("list files")

    assert result.command == "ls -la"


def test_ask_llm_custom_model():
    client = _mock_client("echo hello")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
    ):
        result = ask_llm("say hello", model="llama3")

    assert client.chat.call_args.kwargs["model"] == "llama3"
    assert result.command == "echo hello"


def test_ask_llm_empty_response():
    client = _mock_client("")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
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
    client = _mock_client("EXPLANATION: Lists files sorted by size\nCOMMAND: ls -lS /tmp")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        result = ask_llm("list files by size", verbose=True)

    assert result == LLMResponse(command="ls -lS /tmp", explanation="Lists files sorted by size")


def test_ask_llm_verbose_fallback_when_no_markers():
    """If LLM doesn't follow format, treat whole response as command."""
    client = _mock_client("ls -lS /tmp")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        result = ask_llm("list files by size", verbose=True)

    assert result == LLMResponse(command="ls -lS /tmp")


def test_ask_llm_verbose_uses_different_system_prompt():
    client = _mock_client("EXPLANATION: test\nCOMMAND: echo hi")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        ask_llm("say hi", verbose=True)

    system_msg = client.chat.call_args.kwargs["messages"][0]["content"]
    assert "EXPLANATION" in system_msg
    assert "COMMAND" in system_msg


def test_ask_llm_uses_timeout_from_config():
    client = _mock_client("echo hi")

    with (
        patch("ai_cli.llm.Client", return_value=client) as mock_client_cls,
        patch("ai_cli.llm.load_config", return_value={"timeout": 30}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        ask_llm("say hi")

    mock_client_cls.assert_called_once_with(timeout=30)


def test_ask_llm_default_timeout():
    client = _mock_client("echo hi")

    with (
        patch("ai_cli.llm.Client", return_value=client) as mock_client_cls,
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        ask_llm("say hi")

    mock_client_cls.assert_called_once_with(timeout=20)


def test_ask_llm_prints_model_to_stderr(capsys):
    client = _mock_client("echo hi")

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        ask_llm("say hi")

    captured = capsys.readouterr()
    assert "using glm-5:cloud" in captured.err


def test_ask_llm_custom_system_prompt():
    client = _mock_client("echo hi")
    custom_prompt = "Custom prompt. System: {os} {arch} {shell}. {env_context}Answer with command."

    with (
        patch("ai_cli.llm.Client", return_value=client),
        patch("ai_cli.llm.load_config", return_value={"system_prompt": custom_prompt}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        ask_llm("say hi")

    system_msg = client.chat.call_args.kwargs["messages"][0]["content"]
    assert "Custom prompt" in system_msg


def test_resolve_model_explicit():
    assert _resolve_model("llama3") == "llama3"


def test_resolve_model_env_var():
    with patch.dict("os.environ", {"AI_MODEL": "codellama:7b"}):
        assert _resolve_model() == "codellama:7b"


def test_resolve_model_from_models_list():
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("ai_cli.llm.load_config", return_value={"models": ["model-a", "model-b"]}),
        patch("ai_cli.llm._get_available_models", return_value={"model-b", "model-c"}),
    ):
        assert _resolve_model() == "model-b"


def test_resolve_model_list_with_latest_tag():
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("ai_cli.llm.load_config", return_value={"models": ["mymodel"]}),
        patch("ai_cli.llm._get_available_models", return_value={"mymodel:latest"}),
    ):
        assert _resolve_model() == "mymodel"


def test_resolve_model_list_none_available_falls_to_default():
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("ai_cli.llm.load_config", return_value={"models": ["model-a"], "model": "fallback"}),
        patch("ai_cli.llm._get_available_models", return_value={"other-model"}),
    ):
        assert _resolve_model() == "fallback"


def test_resolve_model_server_unreachable_skips_list():
    with (
        patch.dict("os.environ", {}, clear=True),
        patch(
            "ai_cli.llm.load_config",
            return_value={"models": ["model-a"], "model": "fallback"},
        ),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        assert _resolve_model() == "fallback"


def test_resolve_model_default():
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("ai_cli.llm.load_config", return_value={}),
        patch("ai_cli.llm._get_available_models", return_value=None),
    ):
        assert _resolve_model() == "glm-5:cloud"


def test_default_system_prompt_mentions_oneliner():
    """Default system prompt emphasizes single-line command."""
    from ai_cli.config import DEFAULT_SYSTEM_PROMPT

    assert "single-line" in DEFAULT_SYSTEM_PROMPT or "oneliner" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_mentions_macos_fish():
    """Default system prompt mentions macOS and fish."""
    from ai_cli.config import DEFAULT_SYSTEM_PROMPT

    assert "macOS" in DEFAULT_SYSTEM_PROMPT
    assert "fish" in DEFAULT_SYSTEM_PROMPT

"""LLM integration via ollama SDK."""

import os
import platform
import re
import shutil
from typing import NamedTuple

import click
from ollama import Client
from ollama import list as ollama_list

from ai_cli.config import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_VERBOSE_SYSTEM_PROMPT,
    get_models,
    get_system_prompt,
    get_timeout,
    load_config,
)


class LLMResponse(NamedTuple):
    """Structured response from the LLM."""

    command: str
    explanation: str | None = None


DEFAULT_MODEL = "glm-5:cloud"


def _detect_env() -> dict[str, str]:
    """Detect OS, architecture, shell, and available tools."""
    shell = os.path.basename(os.environ.get("SHELL", "sh"))
    tools = []
    if shutil.which("brew"):
        tools.append("Homebrew")
    if shutil.which("uv"):
        tools.append("uv")
    if shutil.which("docker"):
        tools.append("Docker")
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    env_parts = []
    if tools:
        env_parts.append(f"Available tools: {', '.join(tools)}. ")
    env_parts.append(f"Working directory: {cwd}. Home: {home}. ")
    user_context = load_config().get("context", "")
    if user_context:
        env_parts.append(f"{user_context} ")
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "shell": shell,
        "env_context": "".join(env_parts),
    }


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences wrapping a command."""
    text = re.sub(r"^```(?:\w*)\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _parse_verbose_response(content: str) -> LLMResponse:
    """Parse EXPLANATION/COMMAND format. Fallback: treat whole content as command."""
    explanation_lines: list[str] = []
    command_lines: list[str] = []
    current: list[str] | None = None

    for line in content.strip().splitlines():
        if line.startswith("COMMAND:"):
            command_lines = [line[len("COMMAND:") :].strip()]
            current = command_lines
        elif line.startswith("EXPLANATION:"):
            explanation_lines = [line[len("EXPLANATION:") :].strip()]
            current = explanation_lines
        elif current is not None:
            current.append(line)

    if command_lines:
        command = "\n".join(command_lines).strip()
    else:
        command = content

    explanation = "\n".join(explanation_lines).strip() or None

    command = _strip_markdown_fences(command)
    return LLMResponse(command=command, explanation=explanation)


def _resolve_model(explicit_model: str | None = None) -> str:
    """Resolve which model to use.

    Priority: explicit_model > AI_MODEL env > first available from config models list > config model > default.
    """
    if explicit_model:
        return explicit_model

    env_model = os.environ.get("AI_MODEL")
    if env_model:
        return env_model

    config = load_config()

    # Try models list (priority order) — pick first available
    models_list = get_models(config)
    if models_list:
        available = _get_available_models()
        if available is not None:
            for m in models_list:
                if m in available or (":" not in m and f"{m}:latest" in available):
                    return m
            # None available from list — fall through to single model / default

    return config.get("model", DEFAULT_MODEL)


def _get_available_models() -> set[str] | None:
    """Get set of installed model names, or None if server unreachable."""
    try:
        response = ollama_list()
        return {m.model for m in response.models}
    except ConnectionError:
        return None


def ask_llm(task: str, model: str | None = None, verbose: bool = False) -> LLMResponse | None:
    """Ask ollama to generate a shell command for the given task."""
    resolved_model = _resolve_model(model)

    # Print which model we're using
    click.secho(f"using {resolved_model}", fg="bright_black", err=True)

    config = load_config()
    timeout = get_timeout(config)

    # Build system prompt
    custom_prompt = get_system_prompt(config, verbose=verbose)
    if custom_prompt:
        template = custom_prompt
    elif verbose:
        template = DEFAULT_VERBOSE_SYSTEM_PROMPT
    else:
        template = DEFAULT_SYSTEM_PROMPT

    env = _detect_env()
    system_prompt = template.format(**env)

    client = Client(timeout=timeout)
    response = client.chat(
        model=resolved_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ],
    )

    content = response.message.content.strip()
    if not content:
        return None

    if verbose:
        return _parse_verbose_response(content)

    return LLMResponse(command=_strip_markdown_fences(content))

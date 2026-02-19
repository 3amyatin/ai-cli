"""LLM integration via ollama SDK."""

import os
import platform
import re
from typing import NamedTuple

from ollama import chat


class LLMResponse(NamedTuple):
    """Structured response from the LLM."""

    command: str
    explanation: str | None = None

SYSTEM_PROMPT_TEMPLATE = (
    "You are a terminal assistant. "
    "The user's system: {os} ({arch}), shell: {shell}. "
    "Answer ONLY with a shell command for this system — single line. "
    "No explanations, no markdown, no backticks."
)

VERBOSE_SYSTEM_PROMPT_TEMPLATE = (
    "You are a terminal assistant. "
    "The user's system: {os} ({arch}), shell: {shell}. "
    "First explain briefly what the command does, then give the command. "
    "Format your response exactly as:\n"
    "EXPLANATION: <brief explanation>\n"
    "COMMAND: <single line shell command>\n"
    "No markdown, no backticks."
)

DEFAULT_MODEL = "qwen2.5:7b"


def _detect_env() -> dict[str, str]:
    """Detect OS, architecture, and shell."""
    shell = os.path.basename(os.environ.get("SHELL", "sh"))
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "shell": shell,
    }


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

    # Strip markdown fences from command
    command = re.sub(r"^```(?:\w*)\n?", "", command)
    command = re.sub(r"\n?```$", "", command)
    return LLMResponse(command=command.strip(), explanation=explanation)


def ask_llm(
    task: str, model: str | None = None, verbose: bool = False
) -> LLMResponse | None:
    """Ask ollama to generate a shell command for the given task."""
    model = model or os.environ.get("AI_MODEL", DEFAULT_MODEL)
    template = VERBOSE_SYSTEM_PROMPT_TEMPLATE if verbose else SYSTEM_PROMPT_TEMPLATE
    system_prompt = template.format(**_detect_env())

    response = chat(
        model=model,
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

    # Strip markdown code fences if LLM ignores instructions
    content = re.sub(r"^```(?:\w*)\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return LLMResponse(command=content.strip())

"""LLM integration via ollama SDK."""

import os
import platform
import re

from ollama import chat

SYSTEM_PROMPT_TEMPLATE = (
    "You are a terminal assistant. "
    "The user's system: {os} ({arch}), shell: {shell}. "
    "Answer ONLY with a shell command for this system — single line. "
    "No explanations, no markdown, no backticks."
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


def ask_llm(task: str, model: str | None = None) -> str | None:
    """Ask ollama to generate a shell command for the given task."""
    model = model or os.environ.get("AI_MODEL", DEFAULT_MODEL)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(**_detect_env())

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

    # Strip markdown code fences if LLM ignores instructions
    content = re.sub(r"^```(?:\w*)\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return content.strip()

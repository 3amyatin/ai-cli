"""LLM integration via ollama SDK."""

import os
import re

from ollama import chat

SYSTEM_PROMPT = (
    "You are a terminal assistant. "
    "Answer ONLY with a bash command — single line. "
    "No explanations, no markdown, no backticks."
)

DEFAULT_MODEL = "qwen2.5:7b"


def ask_llm(task: str, model: str | None = None) -> str | None:
    """Ask ollama to generate a bash command for the given task."""
    model = model or os.environ.get("AI_MODEL", DEFAULT_MODEL)

    response = chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
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

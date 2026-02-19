# AI CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a UV-installable CLI tool `ai` that generates bash commands from natural language using ollama.

**Architecture:** Single module `src/ai_cli/cli.py` with click CLI entry point. Uses ollama Python SDK for LLM calls. Packaged with `pyproject.toml` for `uv tool install`.

**Tech Stack:** Python 3.12+, ollama SDK, click, pytest, ruff

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/ai_cli/__init__.py`
- Create: `src/ai_cli/cli.py` (stub)
- Create: `tests/__init__.py`
- Create: `tests/test_cli.py` (stub)

**Step 1: Create pyproject.toml**

```toml
[project]
name = "ai-cli"
version = "0.1.0"
description = "AI-powered bash command generator using ollama"
requires-python = ">=3.12"
dependencies = [
    "ollama",
    "click",
]

[project.scripts]
ai = "ai_cli.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.hatch.build.targets.wheel]
packages = ["src/ai_cli"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
src = ["src"]
line-length = 100

[dependency-groups]
dev = [
    "pytest",
    "ruff",
]
```

**Step 2: Create src/ai_cli/__init__.py**

```python
"""AI-powered bash command generator."""
```

**Step 3: Create src/ai_cli/cli.py stub**

```python
"""CLI entry point for ai command."""

import click


@click.command()
@click.argument("task", nargs=-1, required=True)
def main(task: tuple[str, ...]) -> None:
    """Generate a bash command from a natural language description."""
    click.echo("Not implemented yet")
```

**Step 4: Create tests/__init__.py and tests/test_cli.py stub**

```python
# tests/__init__.py is empty

# tests/test_cli.py
from click.testing import CliRunner

from ai_cli.cli import main


def test_main_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
```

**Step 5: Install deps and run tests**

Run: `uv sync`
Run: `uv run pytest tests/test_cli.py -v`
Expected: 1 test PASS

**Step 6: Lint**

Run: `uv run ruff check src/ tests/`
Run: `uv run ruff format src/ tests/`

**Step 7: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: scaffold ai-cli project with click entry point"
```

---

### Task 2: LLM integration — ask_llm function

**Files:**
- Create: `src/ai_cli/llm.py`
- Create: `tests/test_llm.py`

**Step 1: Write the failing test**

```python
# tests/test_llm.py
from unittest.mock import patch, MagicMock

from ai_cli.llm import ask_llm


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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_llm.py -v`
Expected: FAIL — `ai_cli.llm` does not exist

**Step 3: Write the implementation**

```python
# src/ai_cli/llm.py
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
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_llm.py -v`
Expected: 4 tests PASS

**Step 5: Lint**

Run: `uv run ruff check src/ tests/ && uv run ruff format src/ tests/`

**Step 6: Commit**

```bash
git add src/ai_cli/llm.py tests/test_llm.py
git commit -m "feat: add LLM integration with ollama SDK"
```

---

### Task 3: CLI with confirm-and-execute flow

**Files:**
- Modify: `src/ai_cli/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing tests**

```python
# tests/test_cli.py
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from ai_cli.cli import main


def test_generates_and_displays_command():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", return_value="ls -la /tmp"):
        result = runner.invoke(main, ["list", "files", "in", "tmp"], input="n\n")

    assert result.exit_code == 0
    assert "ls -la /tmp" in result.output


def test_executes_on_confirmation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ask_llm", return_value="echo hello"),
        patch("ai_cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["say", "hello"], input="y\n")

    assert result.exit_code == 0
    mock_run.assert_called_once()


def test_aborts_on_decline():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", return_value="rm -rf /"):
        result = runner.invoke(main, ["delete", "everything"], input="n\n")

    assert result.exit_code == 0
    assert "Aborted" in result.output or "abort" in result.output.lower()


def test_handles_empty_llm_response():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", return_value=None):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "no command" in result.output.lower() or "error" in result.output.lower()


def test_handles_ollama_connection_error():
    runner = CliRunner()
    with patch("ai_cli.cli.ask_llm", side_effect=Exception("Connection refused")):
        result = runner.invoke(main, ["do", "something"])

    assert result.exit_code == 1
    assert "error" in result.output.lower()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL

**Step 3: Implement the CLI**

```python
# src/ai_cli/cli.py
"""CLI entry point for ai command."""

import subprocess
import sys

import click

from ai_cli.llm import ask_llm


@click.command()
@click.argument("task", nargs=-1, required=True)
def main(task: tuple[str, ...]) -> None:
    """Generate a bash command from a natural language description."""
    task_str = " ".join(task)

    try:
        command = ask_llm(task_str)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    if not command:
        click.secho("Error: no command generated", fg="red", err=True)
        sys.exit(1)

    click.secho(f"\n  {command}\n", fg="yellow", bold=True)

    if click.confirm("Execute?", default=False):
        result = subprocess.run(command, shell=True)
        sys.exit(result.returncode)
    else:
        click.echo("Aborted.")
```

**Step 4: Fix test imports (subprocess mock path)**

The test for `test_executes_on_confirmation` patches `ai_cli.cli.subprocess.run`. Verify this path is correct since we import subprocess at module level.

**Step 5: Run tests**

Run: `uv run pytest tests/test_cli.py -v`
Expected: 5 tests PASS

**Step 6: Lint**

Run: `uv run ruff check src/ tests/ && uv run ruff format src/ tests/`

**Step 7: Commit**

```bash
git add src/ai_cli/cli.py tests/test_cli.py
git commit -m "feat: add confirm-and-execute CLI flow"
```

---

### Task 4: Integration smoke test and UV tool install

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration tests — verify the tool installs and runs."""

from click.testing import CliRunner

from ai_cli.cli import main


def test_help_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Generate a bash command" in result.output


def test_no_args_shows_error():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
```

**Step 2: Run tests**

Run: `uv run pytest tests/ -v`
Expected: all tests PASS

**Step 3: Verify UV tool install works**

Run: `uv tool install -e .`
Run: `ai --help`
Expected: help text displayed
Run: `uv tool uninstall ai-cli`

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests and verify uv tool install"
```

---

### Task 5: Documentation and cleanup

**Files:**
- Create: `README.md`
- Create: `CLAUDE.md`

**Step 1: Write README.md**

```markdown
# ai-cli

AI-powered bash command generator using ollama.

Describe what you need in natural language, get a bash command back.

## Requirements

- Python 3.12+
- [ollama](https://ollama.ai/) running locally with `qwen2.5:7b` model

## Install

```bash
ollama pull qwen2.5:7b
uv tool install git+https://github.com/3amyatin/ai-cli
```

## Usage

```bash
ai list all jpg files larger than 10mb
ai compress directory into tar.gz
ai find all python files modified today
```

The tool displays the generated command and asks for confirmation before executing.

## Configuration

- `AI_MODEL` — ollama model name (default: `qwen2.5:7b`)
- `OLLAMA_HOST` — ollama server URL (default: `http://localhost:11434`)

## Development

```bash
git clone https://github.com/3amyatin/ai-cli
cd ai-cli
uv sync
uv run pytest
uv run ruff check src/ tests/
```
```

**Step 2: Write CLAUDE.md**

```markdown
# ai-cli

AI-powered bash command generator using ollama.

## Structure

- `src/ai_cli/cli.py` — click CLI entry point, confirm-and-execute flow
- `src/ai_cli/llm.py` — ollama SDK integration
- `tests/` — pytest tests with mocked ollama calls

## Commands

- Test: `uv run pytest`
- Lint: `uv run ruff check src/ tests/`
- Format: `uv run ruff format src/ tests/`
- Install as tool: `uv tool install -e .`

## Config

- `AI_MODEL` env var (default: `qwen2.5:7b`)
- `OLLAMA_HOST` env var (default: `http://localhost:11434`)
```

**Step 3: Run full test suite and lint**

Run: `uv run pytest tests/ -v`
Run: `uv run ruff check src/ tests/`

**Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: add README and CLAUDE.md"
```

---

### Task 6: GitHub repo setup

**Step 1: Create GitHub repo and push**

```bash
gh repo create ai-cli --public --source=. --push
```

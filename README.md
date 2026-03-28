# ai-cli

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/3amyatin/ai-cli)
[![CI](https://img.shields.io/github/actions/workflow/status/3amyatin/ai-cli/ci.yml?branch=main)](https://github.com/3amyatin/ai-cli/actions)
[![License: MIT](https://img.shields.io/github/license/3amyatin/ai-cli)](https://github.com/3amyatin/ai-cli/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.12-blue)](https://github.com/3amyatin/ai-cli)

AI-powered bash command generator using ollama.

Describe what you need in natural language, get a bash command back.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) — fast Python package manager
- [ollama](https://github.com/ollama/ollama) — local LLM runtime

## Install

Install uv (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install ollama (the model will be downloaded on first run):

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Install ai-cli:

```bash
uv tool install git+https://github.com/3amyatin/ai-cli
```

To upgrade to the latest version:

```bash
uv tool upgrade ai-cli
```

## Usage

```bash
ai list all jpg files larger than 10mb
ai compress directory into tar.gz
ai find all python files modified today
```

The tool displays the generated command and prompts: **[E]xecute** (run it), **[C]opy** (copy to clipboard), or **[A]bort**.

## Options

- `-v` — show explanation before the command
- `-m MODEL` — use a specific model for this run
- `-M MODEL` — use a specific model and save it as default
- `-i` / `--interactive` — interactively pick a model and save it as default
- `--` — separator: everything after is task text, not parsed as options

## Configuration

Settings are stored in `~/.config/ai-cli/config.toml`:

```toml
model = "qwen2.5:7b"
```

Environment variables:
- `AI_MODEL` — ollama model name (overrides config file)
- `OLLAMA_HOST` — ollama server URL (default: `http://localhost:11434`)

Priority: `-m`/`-M` flag > `-i` > `AI_MODEL` env var > config file > `qwen2.5:7b`

## Alternative models

The default model is `qwen2.5:7b`, but you can use any model available in ollama — both [local](https://ollama.com/search?q=coding) and [cloud-hosted](https://ollama.com/search?c=cloud) (no local GPU required).

To switch the model for one run:

```bash
ai -m gemini-3-flash-preview find large files in home directory
```

To switch and save as default:

```bash
ai -M glm-5:cloud find large files in home directory
```

Cloud models tested with ai-cli (March 2026):

| Model | Avg latency | Notes |
|-------|-------------|-------|
| `qwen2.5:7b` (local, default) | ~2s | fast, consistent |
| `gemini-3-flash-preview` (cloud) | ~3s | fast, occasional artifacts |
| `glm-5:cloud` | 2-21s | good quality, inconsistent latency |
| `qwen3.5:cloud` | ~19s | good quality, slow |

To find the best local model for your hardware, try [llm-checker](https://github.com/Pavelevich/llm-checker):

```bash
uvx llm-checker
```

## How it works

1. You describe a task in natural language: `ai find large files in home directory`
2. The CLI sends your prompt to an ollama model (local or cloud)
3. The model returns a bash command (and optionally an explanation with `-v`)
4. The CLI shows the command and asks for confirmation before executing

Limitations:
- Requires a running ollama instance (local or remote via `OLLAMA_HOST`)
- Output quality depends on the chosen model and prompt clarity
- Generated commands target the detected shell — may need adaptation for other shells
- Cloud model latency depends on network and provider load

## Development

Clone and set up the dev environment:

```bash
git clone https://github.com/3amyatin/ai-cli
cd ai-cli
uv sync
```

Install as editable uv tool — the `ai` command links directly to your source code, so any code changes take effect immediately without reinstalling:

```bash
uv tool install -e .
```

Run tests and lint:

```bash
just test        # or: uv run pytest
just lint        # or: uv run ruff check ai_cli/ tests/
just fmt         # or: uv run ruff format ai_cli/ tests/
just check       # lint + format
```

Other useful recipes:

```bash
just             # list all available recipes
just run <args>  # run the CLI via uv (e.g., just run -v list files)
just update      # upgrade and sync dependencies
just fix         # auto-fix lint issues
```

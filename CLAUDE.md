# ai-cli

AI-powered bash command generator using ollama.

Version: 0.2.0

## How it works

1. User describes a task in natural language: `ai find large files`
2. CLI sends prompt to an ollama model (local or cloud)
3. Model returns a bash command (and explanation with `-v`)
4. CLI shows the command and asks for confirmation before executing

Supports both local and [cloud-hosted](https://ollama.com/search?c=cloud) ollama models.
Setup check handles implicit `:latest` tag (e.g. `gemini-3-flash-preview` matches `gemini-3-flash-preview:latest`).

## Structure

- `ai_cli/__init__.py` — package version
- `ai_cli/cli.py` — click CLI entry point, confirm-and-execute flow
- `ai_cli/llm.py` — ollama SDK integration, LLMResponse type, verbose parsing
- `ai_cli/config.py` — persistent config (~/.config/ai-cli/config.toml)
- `ai_cli/setup.py` — runtime checks (ollama reachability, model availability, RAM warning)
- `tests/` — pytest tests with mocked ollama calls

## CLI flags

- `-m MODEL` — use a specific model for this run
- `-M MODEL` — use a specific model and save it as default
- `-i`/`--interactive` — interactively pick a model and save as default
- `-v`/`--verbose` — show LLM command explanation
- `--version` — show version
- `--` — separator between options and task text

## Config

- Settings file: `~/.config/ai-cli/config.toml`
- Default model: `glm-5:cloud` (cloud-hosted, fastest in benchmarks)
- Model priority: `-m`/`-M` flag > `-i` > `AI_MODEL` env var > first available from `models` list > `model` field > `glm-5:cloud`
- Best local alternative: `qwen2.5:7b` (no network dependency)
- `models` field: ordered list of models by priority; first available (installed) model is used
- `model` field: single fallback model (used when no models from list are available)
- `timeout` field: per-model timeout in seconds (default: 20)
- `system_prompt` field: custom system prompt template with placeholders `{os}`, `{arch}`, `{shell}`, `{env_context}`
- `verbose_system_prompt` field: custom prompt for verbose mode (same placeholders)
- `context` field: custom user environment info appended to system prompt (server names, paths, preferences)
- History log: `~/.config/ai-cli/history.jsonl` — records every interaction (task, model, command, action)
- `OLLAMA_HOST` env var (default: `http://localhost:11434`)
- Always prints "using <model>" to stderr before calling LLM

## Development

The tool is installed as an editable uv tool (`uv tool install -e .`), so the `ai` command links directly to source code in this directory. Code changes take effect immediately.

Commands (via justfile):

- `just test` — run pytest
- `just lint` — ruff check
- `just fmt` — ruff format
- `just check` — lint + format
- `just fix` — auto-fix lint issues
- `just run <args>` — run the CLI via uv
- `just update` — upgrade and sync dependencies
- `just install` — reinstall as editable uv tool

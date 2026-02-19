# ai-cli

AI-powered bash command generator using ollama.

Version: 0.2.0

## Structure

- `ai_cli/__init__.py` — package version
- `ai_cli/cli.py` — click CLI entry point, confirm-and-execute flow
- `ai_cli/llm.py` — ollama SDK integration, LLMResponse type, verbose parsing
- `ai_cli/config.py` — persistent config (~/.config/ai-cli/config.toml)
- `ai_cli/setup.py` — runtime checks (ollama reachability, model availability, RAM warning)
- `tests/` — pytest tests with mocked ollama calls

## Commands

- Test: `uv run pytest`
- Lint: `uv run ruff check ai_cli/ tests/`
- Format: `uv run ruff format ai_cli/ tests/`
- Install as tool: `uv tool install -e .`

## CLI flags

- `-m MODEL` — use a specific model for this run
- `-M MODEL` — use a specific model and save it as default
- `-i`/`--interactive` — interactively pick a model and save as default
- `-v`/`--verbose` — show LLM command explanation
- `--version` — show version
- `--` — separator between options and task text

## Config

- Settings file: `~/.config/ai-cli/config.toml`
- Priority: `-m`/`-M` flag > `-i` > `AI_MODEL` env var > config file > `qwen2.5:7b`
- `OLLAMA_HOST` env var (default: `http://localhost:11434`)

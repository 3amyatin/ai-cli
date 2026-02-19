# ai-cli

AI-powered bash command generator using ollama.

Version: 0.2.0

## Structure

- `ai_cli/cli.py` — click CLI entry point, confirm-and-execute flow
- `ai_cli/llm.py` — ollama SDK integration
- `ai_cli/config.py` — config file management (~/.config/ai-cli/config.toml)
- `ai_cli/setup.py` — runtime checks (ollama reachability, model availability)
- `tests/` — pytest tests with mocked ollama calls

## Commands

- Test: `uv run pytest`
- Lint: `uv run ruff check ai_cli/ tests/`
- Format: `uv run ruff format ai_cli/ tests/`
- Install as tool: `uv tool install -e .`

## Config

- Settings file: `~/.config/ai-cli/config.toml`
- `AI_MODEL` env var overrides config file
- `-m`/`-M` flags override everything
- Default model: `qwen2.5:7b`
- `OLLAMA_HOST` env var (default: `http://localhost:11434`)

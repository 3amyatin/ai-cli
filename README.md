# ai-cli

AI-powered bash command generator using ollama.

Describe what you need in natural language, get a bash command back.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — fast Python package manager
- [ollama](https://ollama.ai/) — local LLM runtime

## Install

Install uv (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install ollama and pull the model:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
```

Install ai-cli:

```bash
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

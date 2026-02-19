# ai-cli

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
uv tool install --force git+https://github.com/3amyatin/ai-cli
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

## Alternative models

The default model is `qwen2.5:7b`, but you can use any [coding model](https://ollama.com/search?q=coding) available in ollama. There are also [cloud-hosted models](https://ollama.com/search?c=cloud&q=coding) that don't require local GPU.

To switch the model:

```bash
AI_MODEL=codellama:7b ai find large files in home directory
```

To find the best local model for your hardware, try [llm-checker](https://github.com/Pavelevich/llm-checker):

```bash
uvx llm-checker
```

## Development

```bash
git clone https://github.com/3amyatin/ai-cli
cd ai-cli
uv sync
uv run pytest
uv run ruff check ai_cli/ tests/
```

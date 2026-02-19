# AI CLI Tool Design

Date: 2026-02-19
Status: Approved

## Purpose

A command-line tool `ai` that generates bash commands from natural language descriptions using a local LLM via ollama. Inspired by [habr.com/ru/articles/1001214](https://habr.com/ru/articles/1001214/).

## Architecture

Single Python module packaged as a UV-installable tool.

## Flow

```
ai <task description in any language>
  -> ollama SDK call (system prompt: "respond only with a bash command")
  -> display command in yellow
  -> prompt Y/n
  -> execute via subprocess on approval
```

## Configuration

- `AI_MODEL` env var, default `qwen2.5:7b`
- `OLLAMA_HOST` env var (native to ollama SDK), default `http://localhost:11434`

## Dependencies

- `ollama` - official Python SDK
- `click` - CLI framework

## Project structure

```
ai-cli/
  pyproject.toml
  src/ai_cli/__init__.py
  src/ai_cli/cli.py
  tests/__init__.py
  tests/test_cli.py
  README.md
  CLAUDE.md
```

## Entry point

`[project.scripts] ai = "ai_cli.cli:main"`

## Error handling

- Ollama connection failure -> friendly error message
- Empty LLM response -> error message
- Command execution failure -> show exit code

## Language

System prompt in English, accepts queries in any language.

# ai-cli feature batch design

## Features

### 1. Config file (`~/.config/ai-cli/config.toml`)

```toml
model = "qwen2.5:7b"
```

- Read with `tomllib` (stdlib), write with `tomli_w`
- New module `ai_cli/config.py` — load/save config
- Priority: `-m` flag > `AI_MODEL` env > config file > hardcoded default

### 2. Model selection flags

`-m` (one-time):
- `-m llama3 <task>` — use model for this run only
- `-m <task>` (no value) — list installed models, interactive pick, use for this run

`-M` (persistent):
- `-M llama3 <task>` — save to config and use
- `-M` (no value) — list models, interactive pick, save to config

### 3. Verbose mode (`-v`)

```
ai -v find large files

  This command uses `find` to locate files larger than 100MB...

  find / -size +100M -type f

Execute? [Y/n]:
```

Single LLM call requesting both explanation and command. Parse structured response.

### 4. Model size warning

Before downloading a missing model, query ollama for model info to get size.
Compare against system RAM via `psutil.virtual_memory().total`.
If model > RAM, show warning with sizes and confirm with default=N.

### 5. `--` separator

Everything after `--` is treated as task text, not parsed as options.
Use `click.argument("task", nargs=-1, type=click.UNPROCESSED)`.

### 6. Execute default=Y

Change `click.confirm("Execute?", default=False)` to `default=True`.

## Architecture

```
ai_cli/
  cli.py      — -m, -M, -v flags, -- support, Execute? default=Y
  config.py   — NEW: load/save ~/.config/ai-cli/config.toml
  llm.py      — verbose prompt variant, return (command, explanation) or command
  setup.py    — model size vs RAM check in download confirmation
```

## Dependencies

- `tomli_w` — TOML writing (tomllib is read-only in stdlib)
- `psutil` — system RAM detection

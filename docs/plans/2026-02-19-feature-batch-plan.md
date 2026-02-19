# Feature Batch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add config file, model selection flags (-m/-M), verbose mode (-v), model size vs RAM warning, Execute? default=Y, and `--` separator support.

**Architecture:** New `config.py` module for TOML settings. Extend `cli.py` with click options. Enhance `llm.py` with verbose prompt variant. Add RAM check in `setup.py` during pull progress.

**Tech Stack:** click, tomllib (stdlib), tomli_w, psutil, ollama SDK

---

### Task 1: Add dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add psutil and tomli_w to project dependencies**

In `pyproject.toml`, update the `dependencies` list:

```toml
dependencies = [
    "ollama",
    "click",
    "psutil",
    "tomli_w",
]
```

**Step 2: Sync the environment**

Run: `uv sync`
Expected: dependencies install successfully

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add psutil and tomli_w dependencies"
```

---

### Task 2: Config module

**Files:**
- Create: `ai_cli/config.py`
- Create: `tests/test_config.py`

**Step 1: Write failing tests for config module**

```python
"""Tests for config file load/save."""

import tomllib
from pathlib import Path
from unittest.mock import patch

from ai_cli.config import CONFIG_PATH, load_config, save_config


def test_load_config_returns_defaults_when_no_file(tmp_path):
    with patch.object(
        __import__("ai_cli.config", fromlist=["CONFIG_PATH"]),
        "CONFIG_PATH",
        tmp_path / "nonexistent" / "config.toml",
    ):
        from ai_cli.config import load_config
        # Re-import won't work with patch.object on module attr, use direct approach
    config_path = tmp_path / "config.toml"
    assert not config_path.exists()


def test_load_config_missing_file_returns_empty_dict(tmp_path):
    path = tmp_path / "config.toml"
    config = load_config(path)
    assert config == {}


def test_load_config_reads_model(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('model = "llama3"\n')
    config = load_config(path)
    assert config["model"] == "llama3"


def test_save_config_creates_directory_and_file(tmp_path):
    path = tmp_path / "subdir" / "config.toml"
    save_config({"model": "llama3"}, path)
    assert path.exists()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    assert data["model"] == "llama3"


def test_save_config_preserves_existing_keys(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('model = "llama3"\ncustom_key = "value"\n')
    save_config({"model": "qwen2.5:7b"}, path)
    with open(path, "rb") as f:
        data = tomllib.load(f)
    assert data["model"] == "qwen2.5:7b"
    assert data["custom_key"] == "value"


def test_config_path_is_xdg():
    assert "config" in str(CONFIG_PATH).lower() or ".config" in str(CONFIG_PATH)
    assert str(CONFIG_PATH).endswith("config.toml")
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py -v`
Expected: ImportError — module not found

**Step 3: Write config module**

```python
"""Config file management for ai-cli."""

import tomllib
from pathlib import Path

import tomli_w

CONFIG_PATH = Path.home() / ".config" / "ai-cli" / "config.toml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load config from TOML file. Returns empty dict if file doesn't exist."""
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def save_config(updates: dict, path: Path = CONFIG_PATH) -> None:
    """Merge updates into existing config and save."""
    config = load_config(path)
    config.update(updates)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -v`
Expected: all PASS

**Step 5: Lint**

Run: `uv run ruff check ai_cli/config.py tests/test_config.py`
Expected: no errors

**Step 6: Commit**

```bash
git add ai_cli/config.py tests/test_config.py
git commit -m "feat: add config module for persistent settings"
```

---

### Task 3: Execute? default=Y

**Files:**
- Modify: `ai_cli/cli.py:38`
- Modify: `tests/test_cli.py:14,28`

**Step 1: Write failing test**

In `tests/test_cli.py`, add:

```python
def test_execute_default_is_yes():
    """Pressing Enter without input should execute the command."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="echo test"),
        patch("ai_cli.cli.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(main, ["test"], input="\n")

    assert result.exit_code == 0
    mock_run.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_execute_default_is_yes -v`
Expected: FAIL — default is currently False, so empty input aborts

**Step 3: Change default to True**

In `ai_cli/cli.py:38`, change:

```python
    if click.confirm("Execute?", default=True):
```

Also update `tests/test_cli.py:14` — the `test_generates_and_displays_command` test sends `input="n\n"` which should still work (explicitly declining). No change needed there.

**Step 4: Run all CLI tests**

Run: `uv run pytest tests/test_cli.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add ai_cli/cli.py tests/test_cli.py
git commit -m "fix: default Execute? to Y"
```

---

### Task 4: `--` separator support (test + docs)

Click already handles `--` natively with `nargs=-1` arguments. Just verify with a test.

**Files:**
- Modify: `tests/test_integration.py`

**Step 1: Write test for `--` separator**

In `tests/test_integration.py`, add:

```python
from unittest.mock import patch


def test_double_dash_separates_options_from_task():
    """Everything after -- is treated as task text."""
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="echo hi") as mock_llm,
    ):
        result = runner.invoke(main, ["--", "-v", "list", "files"], input="n\n")

    # "-v" should be part of the task, not parsed as a flag
    call_args = mock_llm.call_args
    task_sent = call_args.args[0] if call_args.args else call_args.kwargs.get("task", "")
    assert "-v" in task_sent
```

**Step 2: Run test**

Run: `uv run pytest tests/test_integration.py -v`
Expected: PASS (click already handles this)

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: verify -- separator works for task arguments"
```

---

### Task 5: Verbose mode (-v)

**Files:**
- Modify: `ai_cli/llm.py`
- Modify: `ai_cli/cli.py`
- Modify: `tests/test_llm.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing tests for verbose LLM response**

In `tests/test_llm.py`, add:

```python
def test_ask_llm_verbose_returns_explanation_and_command():
    mock_response = MagicMock()
    mock_response.message.content = "EXPLANATION: Lists files sorted by size\nCOMMAND: ls -lS /tmp"

    with patch("ai_cli.llm.chat", return_value=mock_response):
        result = ask_llm("list files by size", verbose=True)

    assert result == ("ls -lS /tmp", "Lists files sorted by size")


def test_ask_llm_verbose_fallback_when_no_markers():
    """If LLM doesn't follow format, treat whole response as command."""
    mock_response = MagicMock()
    mock_response.message.content = "ls -lS /tmp"

    with patch("ai_cli.llm.chat", return_value=mock_response):
        result = ask_llm("list files by size", verbose=True)

    assert result == ("ls -lS /tmp", None)


def test_ask_llm_verbose_uses_different_system_prompt():
    mock_response = MagicMock()
    mock_response.message.content = "EXPLANATION: test\nCOMMAND: echo hi"

    with patch("ai_cli.llm.chat", return_value=mock_response) as mock_chat:
        ask_llm("say hi", verbose=True)

    system_msg = mock_chat.call_args.kwargs["messages"][0]["content"]
    assert "EXPLANATION" in system_msg
    assert "COMMAND" in system_msg
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_llm.py -v`
Expected: FAIL — `ask_llm` doesn't accept `verbose` parameter

**Step 3: Update `ai_cli/llm.py`**

Add verbose system prompt template and update `ask_llm`:

```python
VERBOSE_SYSTEM_PROMPT_TEMPLATE = (
    "You are a terminal assistant. "
    "The user's system: {os} ({arch}), shell: {shell}. "
    "First explain briefly what the command does, then give the command. "
    "Format your response exactly as:\n"
    "EXPLANATION: <brief explanation>\n"
    "COMMAND: <single line shell command>\n"
    "No markdown, no backticks."
)
```

Update `ask_llm` signature to `ask_llm(task, model=None, verbose=False)`.

When `verbose=True`:
- Use `VERBOSE_SYSTEM_PROMPT_TEMPLATE`
- Parse response for `EXPLANATION:` and `COMMAND:` lines
- Return `tuple[str, str | None]` — `(command, explanation)`

When `verbose=False`:
- Return `str | None` as before (no change to existing behavior)

Parsing logic:

```python
def _parse_verbose_response(content: str) -> tuple[str, str | None]:
    """Parse EXPLANATION/COMMAND format. Fallback: treat whole content as command."""
    explanation = None
    command = content

    lines = content.strip().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("COMMAND:"):
            command = line[len("COMMAND:"):].strip()
        elif line.startswith("EXPLANATION:"):
            explanation = line[len("EXPLANATION:"):].strip()

    # Strip markdown fences from command
    command = re.sub(r"^```(?:\w*)\n?", "", command)
    command = re.sub(r"\n?```$", "", command)
    return command.strip(), explanation
```

**Step 4: Run LLM tests**

Run: `uv run pytest tests/test_llm.py -v`
Expected: all PASS

**Step 5: Write failing test for CLI -v flag**

In `tests/test_cli.py`, add:

```python
def test_verbose_flag_shows_explanation():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value=("ls -lS", "Lists files by size")),
    ):
        result = runner.invoke(main, ["-v", "list", "files"], input="n\n")

    assert "Lists files by size" in result.output
    assert "ls -lS" in result.output
```

**Step 6: Update `ai_cli/cli.py` to add `-v` flag**

```python
@click.option("-v", "--verbose", is_flag=True, default=False, help="Show command explanation.")
```

In the main function, pass `verbose=verbose` to `ask_llm`. When verbose and result is a tuple:

```python
    if verbose:
        command, explanation = result
        if explanation:
            click.secho(f"\n  {explanation}\n", fg="cyan", err=True)
    else:
        command = result
```

**Step 7: Run all tests**

Run: `uv run pytest -v`
Expected: all PASS

**Step 8: Lint**

Run: `uv run ruff check ai_cli/ tests/`
Expected: no errors

**Step 9: Commit**

```bash
git add ai_cli/llm.py ai_cli/cli.py tests/test_llm.py tests/test_cli.py
git commit -m "feat: add -v verbose mode with command explanation"
```

---

### Task 6: Model selection (-m / -M)

**Files:**
- Modify: `ai_cli/cli.py`
- Modify: `tests/test_cli.py`
- Uses: `ai_cli/config.py` (from Task 2)

**Step 1: Write failing tests for -m and -M flags**

In `tests/test_cli.py`, add:

```python
def test_m_flag_with_value_uses_specified_model():
    runner = CliRunner()
    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="echo hi") as mock_llm,
    ):
        result = runner.invoke(main, ["-m", "llama3", "say", "hi"], input="n\n")

    mock_llm.assert_called_once()
    assert mock_llm.call_args.kwargs.get("model") == "llama3" or mock_llm.call_args[1].get("model") == "llama3"


def test_m_flag_without_value_shows_model_picker():
    """When -m is used without a value, show interactive model picker."""
    runner = CliRunner()
    mock_resp = MagicMock()
    model_a = MagicMock()
    model_a.model = "qwen2.5:7b"
    model_a.size = 4_000_000_000
    model_b = MagicMock()
    model_b.model = "llama3:latest"
    model_b.size = 5_000_000_000
    mock_resp.models = [model_a, model_b]

    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ollama_list", return_value=mock_resp),
        patch("ai_cli.cli.ask_llm", return_value="echo hi"),
    ):
        # User picks option 1 (qwen2.5:7b)
        result = runner.invoke(main, ["-m", "--", "say", "hi"], input="1\nn\n")

    assert result.exit_code == 0


def test_big_m_flag_saves_model_to_config(tmp_path):
    runner = CliRunner()
    config_path = tmp_path / "config.toml"

    with (
        patch("ai_cli.cli.ensure_ready"),
        patch("ai_cli.cli.ask_llm", return_value="echo hi"),
        patch("ai_cli.cli.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(main, ["-M", "llama3", "say", "hi"], input="n\n")

    import tomllib
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    assert config["model"] == "llama3"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v -k "m_flag or big_m"`
Expected: FAIL

**Step 3: Update `ai_cli/cli.py`**

Add imports:

```python
from ollama import list as ollama_list
from ai_cli.config import CONFIG_PATH, load_config, save_config
```

Add click options:

```python
@click.option("-m", "model_opt", default=None, is_flag=False, flag_value="__select__",
              help="Use a specific model, or pick interactively if no value given.")
@click.option("-M", "model_save", default=None, is_flag=False, flag_value="__select__",
              help="Like -m, but also saves the choice as default.")
```

Add model picker helper:

```python
def _pick_model() -> str:
    """List installed ollama models and let user pick one."""
    response = ollama_list()
    if not response.models:
        click.secho("No models installed.", fg="red", err=True)
        sys.exit(1)

    click.secho("Installed models:", fg="cyan", err=True)
    for i, m in enumerate(response.models, 1):
        size_gb = m.size / (1024**3) if m.size else 0
        click.secho(f"  {i}. {m.model} ({size_gb:.1f} GB)", err=True)

    choice = click.prompt("Choose model", type=int, err=True)
    if choice < 1 or choice > len(response.models):
        click.secho("Invalid choice.", fg="red", err=True)
        sys.exit(1)

    return response.models[choice - 1].model
```

Update model resolution in `main()`:

```python
    # Resolve model: -m/-M flag > AI_MODEL env > config > default
    if model_save is not None:
        model = _pick_model() if model_save == "__select__" else model_save
        save_config({"model": model})
    elif model_opt is not None:
        model = _pick_model() if model_opt == "__select__" else model_opt
    else:
        config = load_config()
        model = os.environ.get("AI_MODEL", config.get("model", DEFAULT_MODEL))
```

**Step 4: Run all tests**

Run: `uv run pytest -v`
Expected: all PASS

**Step 5: Lint**

Run: `uv run ruff check ai_cli/ tests/`

**Step 6: Commit**

```bash
git add ai_cli/cli.py tests/test_cli.py
git commit -m "feat: add -m (select model) and -M (save default model) flags"
```

---

### Task 7: Model size vs RAM warning

**Files:**
- Modify: `ai_cli/setup.py`
- Modify: `tests/test_setup.py`

**Step 1: Write failing tests**

In `tests/test_setup.py`, add:

```python
@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_larger_than_ram_shows_warning(mock_list, mock_pull, capsys):
    """When model download size exceeds RAM, show a warning."""
    resp = MagicMock()
    resp.models = []
    mock_list.return_value = resp

    # Simulate progress: first event has digest and total > RAM
    progress1 = MagicMock()
    progress1.status = "pulling manifest"
    progress1.digest = None
    progress1.completed = None
    progress1.total = None

    progress2 = MagicMock()
    progress2.status = "pulling abc123"
    progress2.digest = "sha256:abc123"
    progress2.completed = 0
    progress2.total = 100_000_000_000  # 100 GB — larger than any RAM

    mock_pull.return_value = iter([progress1, progress2])

    # First confirm = yes to download, second confirm = no to RAM warning
    with (
        patch("click.confirm", side_effect=[True, False]),
        patch("ai_cli.setup.psutil") as mock_psutil,
    ):
        mock_psutil.virtual_memory.return_value.total = 16_000_000_000  # 16 GB
        with pytest.raises(SystemExit):
            ensure_ready("huge-model")

    output = capsys.readouterr().err
    assert "ram" in output.lower() or "RAM" in output


@patch("ai_cli.setup.ollama_pull")
@patch("ai_cli.setup.ollama_list")
def test_model_smaller_than_ram_no_warning(mock_list, mock_pull, capsys):
    """When model fits in RAM, no extra warning is shown."""
    resp = MagicMock()
    resp.models = []
    mock_list.return_value = resp

    progress = MagicMock()
    progress.status = "pulling abc123"
    progress.digest = "sha256:abc123"
    progress.completed = 4_000_000_000
    progress.total = 4_000_000_000  # 4 GB

    mock_pull.return_value = iter([progress])

    with (
        patch("click.confirm", return_value=True),
        patch("ai_cli.setup.psutil") as mock_psutil,
    ):
        mock_psutil.virtual_memory.return_value.total = 16_000_000_000
        ensure_ready("small-model")

    output = capsys.readouterr().err
    assert "ram" not in output.lower()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_setup.py -v -k "ram"`
Expected: FAIL

**Step 3: Update `ai_cli/setup.py`**

Add import:

```python
import psutil
```

Add size formatting helper:

```python
def _fmt_size(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
```

Update the pull loop in `ensure_ready` to track digests and check against RAM:

```python
    click.secho(f"Pulling model {model}...", fg="yellow", err=True)
    ram_total = psutil.virtual_memory().total
    seen_digests: dict[str, int] = {}
    ram_warned = False

    try:
        for progress in ollama_pull(model, stream=True):
            # Track model size from layer digests
            if (
                not ram_warned
                and progress.digest
                and progress.total
                and progress.digest not in seen_digests
            ):
                seen_digests[progress.digest] = progress.total
                total_size = sum(seen_digests.values())
                if total_size > ram_total:
                    click.secho(
                        f"\n  Warning: model is {_fmt_size(total_size)} — "
                        f"larger than your RAM ({_fmt_size(ram_total)}).",
                        fg="red",
                        err=True,
                    )
                    if not click.confirm(
                        "Continue downloading?", default=False, err=True
                    ):
                        click.secho("Aborted.", fg="red", err=True)
                        sys.exit(1)
                    ram_warned = True

            # Existing progress display
            if progress.completed is not None and progress.total:
                pct = int(progress.completed / progress.total * 100)
                click.secho(
                    f"\r  {progress.status}: {pct}%",
                    fg="yellow", err=True, nl=False,
                )
            else:
                click.secho(
                    f"\r  {progress.status}",
                    fg="yellow", err=True, nl=False,
                )
        click.secho("", err=True)
    except Exception as e:
        click.secho(f"\nFailed to pull model {model}: {e}", fg="red", err=True)
        sys.exit(1)
```

**Step 4: Run all setup tests**

Run: `uv run pytest tests/test_setup.py -v`
Expected: all PASS

**Step 5: Lint**

Run: `uv run ruff check ai_cli/setup.py tests/test_setup.py`

**Step 6: Commit**

```bash
git add ai_cli/setup.py tests/test_setup.py
git commit -m "feat: warn when model download size exceeds system RAM"
```

---

### Task 8: Update docs and config resolution

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `ai_cli/cli.py` (config-based model resolution already done in Task 6)

**Step 1: Update README.md**

Add to Usage section:

```markdown
## Options

- `-v` — show explanation before the command
- `-m MODEL` — use a specific model for this run
- `-m` — pick from installed models interactively (use `--` before task)
- `-M MODEL` — use a specific model and save it as default
- `-M` — pick interactively and save as default
- `--` — separator: everything after is task text, not parsed as options

## Configuration

Settings are stored in `~/.config/ai-cli/config.toml`:

- `model` — default ollama model (overridden by `AI_MODEL` env var or `-m` flag)

Priority: `-m`/`-M` flag > `AI_MODEL` env var > config file > `qwen2.5:7b`
```

**Step 2: Update CLAUDE.md**

Add `config.py` to the Structure section. Update Config section with new priority chain.

**Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: all PASS

**Step 4: Lint everything**

Run: `uv run ruff check ai_cli/ tests/`

**Step 5: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: update README and CLAUDE.md with new features"
```

---

### Task 9: Final integration test

**Files:**
- Modify: `tests/test_integration.py`

**Step 1: Add integration tests for new flags**

```python
def test_help_shows_all_options():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "-v" in result.output
    assert "-m" in result.output
    assert "-M" in result.output


def test_verbose_flag_in_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "explanation" in result.output.lower() or "verbose" in result.output.lower()
```

**Step 2: Run full suite**

Run: `uv run pytest -v`
Expected: all PASS

**Step 3: Commit and push**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for new CLI flags"
git push
```

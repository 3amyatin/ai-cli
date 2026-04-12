"""Config file management for ai-cli."""

import tomllib
from pathlib import Path

import tomli_w

CONFIG_PATH = Path.home() / ".config" / "ai-cli" / "config.toml"

DEFAULT_TIMEOUT = 20

DEFAULT_SYSTEM_PROMPT = (
    "You are a terminal command assistant on macOS with fish shell. "
    "The user's system: {os} ({arch}), shell: {shell}. "
    "{env_context}"
    "You MUST answer with a single-line shell command. "
    "The command must be a oneliner — no line breaks, no multi-line scripts. "
    "You may add a brief note before or after the command, but the command itself must be one line. "
    "No markdown, no backticks."
)

DEFAULT_VERBOSE_SYSTEM_PROMPT = (
    "You are a terminal command assistant on macOS with fish shell. "
    "The user's system: {os} ({arch}), shell: {shell}. "
    "{env_context}"
    "First explain briefly what the command does, then give the command. "
    "The command MUST be a single-line oneliner — no line breaks. "
    "Format your response exactly as:\n"
    "EXPLANATION: <brief explanation>\n"
    "COMMAND: <single line shell command>\n"
    "No markdown, no backticks."
)


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load config from TOML file. Returns empty dict if file doesn't exist or is invalid."""
    if not path.exists():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError:
        return {}


def save_config(updates: dict, path: Path = CONFIG_PATH) -> None:
    """Merge updates into existing config and save."""
    config = load_config(path)
    config.update(updates)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)


def get_timeout(config: dict | None = None) -> int:
    """Get timeout in seconds from config, default 20."""
    if config is None:
        config = load_config()
    return config.get("timeout", DEFAULT_TIMEOUT)


def get_models(config: dict | None = None) -> list[str]:
    """Get ordered model list from config."""
    if config is None:
        config = load_config()
    return config.get("models", [])


def get_system_prompt(config: dict | None = None, verbose: bool = False) -> str | None:
    """Get custom system prompt template from config, or None for default."""
    if config is None:
        config = load_config()
    if verbose:
        return config.get("verbose_system_prompt")
    return config.get("system_prompt")

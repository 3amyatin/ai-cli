"""Config file management for ai-cli."""

import tomllib
from pathlib import Path

import tomli_w

CONFIG_PATH = Path.home() / ".config" / "ai-cli" / "config.toml"


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

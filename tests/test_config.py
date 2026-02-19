"""Tests for config file load/save."""

import tomllib

from ai_cli.config import CONFIG_PATH, load_config, save_config


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


def test_load_config_malformed_toml_returns_empty_dict(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("this is not valid [[[ toml")
    config = load_config(path)
    assert config == {}


def test_config_path_is_xdg():
    assert ".config" in str(CONFIG_PATH)
    assert str(CONFIG_PATH).endswith("config.toml")

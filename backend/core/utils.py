import json
import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _resolve_path(relative_path: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    return (base_dir / relative_path).resolve()


def _get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def _load_config() -> dict:
    config_path = _get_repo_root() / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)


def _coerce_env_value(value: str, template: object) -> object:
    if isinstance(template, bool):
        return value.lower() in {"1", "true", "yes", "on"}
    if isinstance(template, int) and not isinstance(template, bool):
        return int(value)
    if isinstance(template, float):
        return float(value)
    return value


def load_prompt(relative_path: str) -> str:
    """Load a prompt relative to the src/ directory."""
    prompt_path = _resolve_path(relative_path)
    with open(prompt_path, "r") as f:
        return f.read()

def load_key(key: str) -> str:
    """Load a key from the environment variables"""
    return os.getenv(key)

def get_config(key: str) -> str:
    """Get a configuration value from repo-root config.json with env overrides."""
    env_key = f"KLTN_{key.upper()}"
    env_value = os.getenv(env_key)
    config = _load_config()
    if env_value is not None:
        template = config.get(key)
        if template is not None:
            return _coerce_env_value(env_value, template)
        return env_value
    return config.get(key)

# # Test
# print(get_config("model_whisper"))
# print(load_key("HF_TOKEN"))
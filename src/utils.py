import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _resolve_path(relative_path: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    return (base_dir / relative_path).resolve()


def load_prompt(relative_path: str) -> str:
    """Load a prompt relative to the src/ directory."""
    prompt_path = _resolve_path(relative_path)
    with open(prompt_path, "r") as f:
        return f.read()

def load_key(key: str) -> str:
    """Load a key from the environment variables"""
    return os.getenv(key)

def get_config(key: str) -> str:
    """Get a configuration value from config.json in this module."""
    config_path = _resolve_path("config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config.get(key)

# # Test
# print(get_config("model_whisper"))
# print(load_key("HF_TOKEN"))
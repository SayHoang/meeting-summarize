import json
import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def _resolve_path(relative_path: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    return (base_dir / relative_path).resolve()


def _get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _load_config() -> dict:
    config_path = _get_repo_root() / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)

def reload_config() -> None:
    _load_config.cache_clear()

def read_config_file() -> dict:
    config_path = _get_repo_root() / "config.json"
    return json.loads(config_path.read_text())

def write_config_file(config: dict) -> None:
    config_path = _get_repo_root() / "config.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    reload_config()


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


# Summarize Utils
def _build_prompt(prompt_text: str, transcript_text: str) -> str:
    return f"{prompt_text}:\n\n{transcript_text}"

def _load_transcript_text(params: dict) -> str:
    transcript_text = params.get("transcript_text")
    transcript_path = params.get("transcript_path")
    if transcript_text:
        return transcript_text
    if transcript_path:
        return Path(transcript_path).read_text()
    raise ValueError("transcript_text or transcript_path is required.")

def _generate_output_filename(input_file: str, output_dir: str) -> str:
    file_name = Path(input_file).stem
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return str(Path(output_dir) / f"summary_{timestamp}.txt")

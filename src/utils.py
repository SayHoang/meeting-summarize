import json
from dotenv import load_dotenv
import os
load_dotenv()

def load_prompt(file_path: str) -> str:
    """Load a prompt from /prompts"""
    with open(file_path, "r") as f:
        return f.read()

def load_key(key: str) -> str:
    """Load a key from the environment variables"""
    return os.getenv(key)

def get_config(key: str) -> str:
    """Get a configuration value from the config file."""
    with open("../src/config.json", "r") as f:
        config = json.load(f)
    return config.get(key)

# # Test
# print(get_config("model_whisper"))
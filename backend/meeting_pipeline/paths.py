from pathlib import Path


def get_backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_storage_root() -> Path:
    return get_backend_root() / "meeting_storage"


def ensure_storage_root() -> Path:
    storage_root = get_storage_root()
    storage_root.mkdir(parents=True, exist_ok=True)
    return storage_root


def get_job_dir(job_id: str) -> Path:
    return ensure_storage_root() / job_id


def get_prompt_override_path() -> Path:
    return ensure_storage_root() / "summary_prompt.txt"

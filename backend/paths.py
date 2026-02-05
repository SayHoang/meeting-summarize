import sys
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_core_on_path() -> None:
    core_dir = Path(__file__).resolve().parents[1] / "core"
    if str(core_dir) not in sys.path:
        sys.path.append(str(core_dir))


def get_storage_root() -> Path:
    _ensure_core_on_path()
    from utils import get_config

    storage_dir = get_config("meeting_storage_dir")
    if not storage_dir:
        return _get_repo_root() / "kltn" / "meeting_storage"

    storage_path = Path(storage_dir)
    if storage_path.is_absolute():
        return storage_path
    return (_get_repo_root() / storage_path).resolve()


def ensure_storage_root() -> Path:
    storage_root = get_storage_root()
    storage_root.mkdir(parents=True, exist_ok=True)
    return storage_root


def get_job_dir(job_id: str) -> Path:
    return ensure_storage_root() / job_id


def get_prompt_override_path() -> Path:
    return ensure_storage_root() / "summary_prompt.txt"

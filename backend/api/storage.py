import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional
from uuid import uuid4

from .paths import get_job_dir, ensure_storage_root, get_prompt_override_path
from .types import JobMeta

_TEXT_ENCODING = "utf-8"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _meta_path(job_dir: Path) -> Path:
    return job_dir / "meta.json"


def create_job(params: dict) -> JobMeta:
    job_id = params.get("job_id") or f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}"
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    meta = JobMeta(
        job_id=job_id,
        original_filename=params.get("original_filename"),
        status="created",
    )
    save_meta({"job_dir": job_dir, "meta": meta})
    return meta


def save_meta(params: dict) -> JobMeta:
    job_dir = params["job_dir"]
    meta = params["meta"]
    meta.updated_at = datetime.now(timezone.utc)
    meta_path = _meta_path(job_dir)
    meta_path.write_text(meta.model_dump_json(indent=2), encoding=_TEXT_ENCODING)
    return meta


def load_meta(params: dict) -> JobMeta:
    job_dir = params["job_dir"]
    meta_path = _meta_path(job_dir)
    if not meta_path.exists():
        raise ValueError(f"meta.json not found for job: {job_dir.name}")
    return JobMeta.model_validate_json(meta_path.read_text(encoding=_TEXT_ENCODING))


def update_meta(params: dict) -> JobMeta:
    job_dir = params["job_dir"]
    updates = params.get("updates", {})
    meta = load_meta({"job_dir": job_dir})
    updated_meta = meta.model_copy(update=updates)
    return save_meta({"job_dir": job_dir, "meta": updated_meta})


def save_audio_bytes(params: dict) -> Path:
    job_id = params["job_id"]
    original_filename = params["original_filename"]
    audio_bytes = params["audio_bytes"]

    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    file_ext = Path(original_filename).suffix.lower()
    audio_path = job_dir / f"input{file_ext}"
    audio_path.write_bytes(audio_bytes)

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "input_path": str(audio_path),
                "original_filename": original_filename,
                "status": "uploaded",
            },
        }
    )
    return audio_path


def save_transcript_text(params: dict) -> Path:
    job_id = params["job_id"]
    transcript_text = params["transcript_text"]
    job_dir = get_job_dir(job_id)
    transcript_path = job_dir / "transcript.txt"
    transcript_path.write_text(transcript_text, encoding=_TEXT_ENCODING)

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "transcript_path": str(transcript_path),
                "transcript_ready": True,
                "status": "transcribed",
            },
        }
    )
    return transcript_path


def save_summary_text(params: dict) -> Path:
    job_id = params["job_id"]
    summary_text = params["summary_text"]
    job_dir = get_job_dir(job_id)
    summary_path = job_dir / "summary.txt"
    summary_path.write_text(summary_text, encoding=_TEXT_ENCODING)

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "summary_path": str(summary_path),
                "summary_ready": True,
                "status": "summarized",
            },
        }
    )
    return summary_path


def save_judge_report_markdown(params: dict) -> Path:
    job_id = params["job_id"]
    report_markdown = params["report_markdown"]
    job_dir = get_job_dir(job_id)
    report_path = job_dir / "full_report.md"
    report_path.write_text(report_markdown, encoding=_TEXT_ENCODING)

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "judge_report_path": str(report_path),
                "judge_ready": True,
            },
        }
    )
    return report_path


def read_text(params: dict) -> str:
    file_path = Path(params["file_path"])
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    return file_path.read_text(encoding=_TEXT_ENCODING)


def list_jobs() -> list[JobMeta]:
    storage_root = ensure_storage_root()
    job_metas: list[JobMeta] = []
    for job_dir in storage_root.iterdir():
        if not job_dir.is_dir():
            continue
        meta_path = _meta_path(job_dir)
        if meta_path.exists():
            job_metas.append(
                JobMeta.model_validate_json(meta_path.read_text(encoding=_TEXT_ENCODING))
            )
    job_metas.sort(key=lambda item: item.created_at, reverse=True)
    return job_metas


def get_prompt_override_text() -> Optional[str]:
    prompt_path = get_prompt_override_path()
    if prompt_path.exists():
        return prompt_path.read_text(encoding=_TEXT_ENCODING)
    return None


def save_prompt_override_text(prompt_text: str) -> Path:
    prompt_path = get_prompt_override_path()
    prompt_path.write_text(prompt_text, encoding=_TEXT_ENCODING)
    return prompt_path

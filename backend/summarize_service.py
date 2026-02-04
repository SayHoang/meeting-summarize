import sys
from pathlib import Path
from typing import Callable, Optional

from .paths import get_job_dir, get_prompt_override_path
from .storage import update_meta
from .types import ProgressEvent, SummarizeParams


def _ensure_src_on_path() -> None:
    src_dir = Path(__file__).resolve().parents[2] / "src"
    if str(src_dir) not in sys.path:
        sys.path.append(str(src_dir))


def _load_prompt_override() -> Optional[str]:
    prompt_path = get_prompt_override_path()
    if prompt_path.exists():
        return prompt_path.read_text()
    return None


def run_summary(
    params: SummarizeParams,
    on_progress: Optional[Callable[[ProgressEvent], None]] = None,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    _ensure_src_on_path()
    from summarize import generate_summary_to_file

    job_dir = get_job_dir(params.job_id)
    prompt_text = params.prompt_text or _load_prompt_override()

    def _progress_callback(event: dict) -> None:
        percent = int(event.get("percent", 0))
        update_meta(
            {
                "job_dir": job_dir,
                "updates": {
                    "progress_summary": percent,
                    "status": "summarizing",
                },
            }
        )
        if on_progress:
            on_progress(
                ProgressEvent(
                    stage="summary",
                    percent=percent,
                    message=event.get("message", "Summarizing..."),
                )
            )

    output_path = generate_summary_to_file(
        {
            "transcript_path": params.transcript_path,
            "output_file": params.output_path,
            "prompt_text": prompt_text,
            "model_name": params.model_name,
        },
        on_progress=_progress_callback,
        on_chunk=on_chunk,
    )

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "summary_path": output_path,
                "summary_ready": True,
                "status": "summarized",
                "progress_summary": 100,
            },
        }
    )
    return output_path

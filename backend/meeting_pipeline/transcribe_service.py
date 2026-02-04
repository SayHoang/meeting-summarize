import sys
from pathlib import Path
from typing import Callable, Optional

from .paths import get_job_dir
from .storage import update_meta
from .types import ProgressEvent, TranscribeParams


def _ensure_src_on_path() -> None:
    src_dir = Path(__file__).resolve().parents[2] / "src"
    if str(src_dir) not in sys.path:
        sys.path.append(str(src_dir))


def run_transcribe(
    params: TranscribeParams, on_progress: Optional[Callable[[ProgressEvent], None]] = None
) -> str:
    _ensure_src_on_path()
    from faster import transcribe_to_file_with_progress

    job_dir = get_job_dir(params.job_id)

    def _progress_callback(event: dict) -> None:
        percent = int(event.get("percent", 0))
        update_meta(
            {
                "job_dir": job_dir,
                "updates": {
                    "progress_transcribe": percent,
                    "status": "transcribing",
                },
            }
        )
        if on_progress:
            on_progress(
                ProgressEvent(
                    stage="transcribe",
                    percent=percent,
                    message=event.get("message", "Transcribing..."),
                )
            )

    output_path = transcribe_to_file_with_progress(
        {
            "input_file": params.input_path,
            "output_file": params.output_path,
            "beam_size": params.beam_size,
            "model_name": params.model_name,
            "device": params.device,
        },
        on_progress=_progress_callback,
    )

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "transcript_path": output_path,
                "transcript_ready": True,
                "status": "transcribed",
                "progress_transcribe": 100,
            },
        }
    )
    return output_path

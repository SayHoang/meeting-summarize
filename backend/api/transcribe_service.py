import sys
from pathlib import Path
from typing import Callable, Optional

from .paths import get_job_dir
from .storage import update_meta
from .types import TranscribeParams


def _ensure_core_on_path() -> None:
    core_dir = Path(__file__).resolve().parents[1] / "core"
    if str(core_dir) not in sys.path:
        sys.path.append(str(core_dir))


def run_transcribe(
    params: TranscribeParams, on_segment: Optional[Callable[[dict], None]] = None
) -> str:
    _ensure_core_on_path()
    from faster import transcribe_audio_stream

    job_dir = get_job_dir(params.job_id)
    output_path = params.output_path
    with open(output_path, "w", encoding="utf-8") as f:
        for event in transcribe_audio_stream(
            {
                "input_file": params.input_path,
                "output_file": params.output_path,
                "beam_size": params.beam_size,
                "model_name": params.model_name,
                "device": params.device,
            }
        ):
            f.write(f"{event['segment_line']}\n")
            if on_segment:
                on_segment(event)

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "transcript_path": output_path,
                "transcript_ready": True,
            },
        }
    )
    return output_path

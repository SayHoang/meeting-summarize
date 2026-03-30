import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, Iterable

from faster_whisper import WhisperModel
from utils import get_config, load_prompt


SUPPORTED_FORMATS = [".mp3", ".mp4", ".wav", ".m4a", ".mov", ".mkv", ".webm"]

@lru_cache(maxsize=2)
def _load_model(model_name: str, device: str) -> WhisperModel:
    compute_type = get_config("compute_type")
    
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def validate_audio_file(file_path: str) -> bool:
    """Validate if the audio file exists and has a supported format."""
    if not os.path.exists(file_path):
        return False
    
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in SUPPORTED_FORMATS


def get_file_info(file_path: str) -> dict:
    """Get information about the audio file."""
    file_name = os.path.basename(file_path)
    extension = os.path.splitext(file_path)[1]
    size_bytes = os.path.getsize(file_path)
    size_mb = round(size_bytes / (1024 * 1024), 2)
    is_valid = validate_audio_file(file_path)
    
    return {
        "file_name": file_name,
        "extension": extension,
        "size_mb": size_mb,
        "is_valid": is_valid
    }

def generate_output_filename(input_file: str, output_dir: str) -> str:
    """Generate output filename based on input file name."""
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # output_file = f"{file_name}_{timestamp}.txt"
    output_file = f"transcript_{timestamp}.txt"
    
    return os.path.join(output_dir, output_file)

def transcribe_audio_stream(params: dict) -> Iterable[Dict[str, object]]:
    """Yield transcript segments as they are produced."""
    input_file = params.get("input_file")
    output_file = params.get("output_file")
    beam_size = params.get("beam_size", 5) or get_config("beam_size")
    vad_filter = params.get("vad_filter", True) or get_config("vad_filter")
    model_name = params.get("model_name") or get_config("model_whisper")
    device = params.get("device") or get_config("device")

    initial_prompt = params.get("initial_prompt") or load_prompt("prompts/initial_prompt.txt")
    
    if not input_file or not output_file:
        raise ValueError("input_file and output_file are required.")

    if not validate_audio_file(input_file):
        raise ValueError(
            f"Invalid audio file: {input_file}. "
            f"File must exist and have one of these extensions: {', '.join(SUPPORTED_FORMATS)}"
        )

    model = _load_model(model_name, device)
    segments, _info = model.transcribe(
        input_file, 
        beam_size=beam_size, 
        vad_filter=vad_filter,
        initial_prompt=initial_prompt
    )

    for segment_index, segment in enumerate(segments, start=1):
        line = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
        yield {
            "segment_line": line,
            "segment_index": segment_index,
            "segment_start": segment.start,
            "segment_end": segment.end,
        }


def transcribe_to_file(params: dict) -> str:
    """Write transcript to file using the streaming generator."""
    output_file = params.get("output_file")
    if not output_file:
        raise ValueError("output_file is required.")

    with open(output_file, "w", encoding="utf-8") as f:
        for event in transcribe_audio_stream(params):
            f.write(f"{event['segment_line']}\n")

    return output_file


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
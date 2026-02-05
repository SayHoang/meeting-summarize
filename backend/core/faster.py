import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, Iterable

from faster_whisper import WhisperModel
# from utils import get_config, load_key
# from pyannote.audio import Pipeline
# from pyannote.core import Annotation
# # import torch
from utils import get_config


SUPPORTED_FORMATS = [".mp3", ".mp4", ".wav", ".m4a", ".mov", ".mkv", ".webm"]

@lru_cache(maxsize=2)
def _load_model(model_name: str, device: str) -> WhisperModel:
    return WhisperModel(model_name, device=device, compute_type="int8")


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
    beam_size = params.get("beam_size", 5)
    model_name = params.get("model_name") or get_config("model_whisper")
    device = params.get("device") or get_config("device")

    if not input_file or not output_file:
        raise ValueError("input_file and output_file are required.")

    if not validate_audio_file(input_file):
        raise ValueError(
            f"Invalid audio file: {input_file}. "
            f"File must exist and have one of these extensions: {', '.join(SUPPORTED_FORMATS)}"
        )

    model = _load_model(model_name, device)
    segments, _info = model.transcribe(input_file, beam_size=beam_size)

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

    with open(output_file, "w") as f:
        for event in transcribe_audio_stream(params):
            f.write(f"{event['segment_line']}\n")

    return output_file

# def transcribe_and_diarize(input_file: str, output_file: str, beam_size: int = 5) -> None:
#     """Transcribe audio and add speaker labels using Pyannote on CPU."""
    
#     print("--- Đang chạy Transcription (Whisper) ---")
#     segments, info = model.transcribe(input_file, beam_size=beam_size)
#     whisper_segments = list(segments)
    
#     print("--- Đang chạy Diarization (Pyannote) - Sẽ tốn thời gian trên CPU ---")
#     hf_token = load_key("HF_TOKEN")
    
#     pipeline = Pipeline.from_pretrained(
#         "pyannote/speaker-diarization-3.1",
#         token=hf_token
#     )
#     # pipeline.to(torch.device("cpu"))
    
#     # ---- DEBUG -----
#     diarization_result = pipeline(input_file)
#     print(f"DEBUG: Type of diarization_result is: {type(diarization_result)}")

#     # # ---- DEBUG -----
#     # if hasattr(diarization_result, "annotation"):
#     #     diarization = diarization_result.annotation
#     # elif hasattr(diarization_result, "diarization"):
#     #     diarization = diarization_result.diarization
#     # elif hasattr(diarization_result, "annotations"):
#     #     diarization = diarization_result.annotations
#     # else:
#     #     raise TypeError(
#     #         f"Unsupported DiarizeOutput structure. "
#     #         f"Available attributes: {dir(diarization_result)}"
#     #     )

#     # print(f"DEBUG: Extracted annotation type: {type(diarization)}")

#     diarization = diarization_result.speaker_diarization

#     final_transcript = []
    
#     for segment in whisper_segments:
#         # Tìm speaker có overlap nhiều nhất với segment này
#         start = segment.start
#         end = segment.end
        
#         # Lấy các đoạn diarization trùng thời gian
#         speakers_overlap = []
#         for turn, _, speaker in diarization.itertracks(yield_label=True):
#             # Tính giao điểm thời gian (Intersection)
#             intersection_start = max(start, turn.start)
#             intersection_end = min(end, turn.end)
            
#             if intersection_end > intersection_start:
#                 duration = intersection_end - intersection_start
#                 speakers_overlap.append((speaker, duration))
        
#         # Chọn speaker có thời gian nói dài nhất trong câu này
#         if speakers_overlap:
#             best_speaker = max(speakers_overlap, key=lambda x: x[1])[0]
#         else:
#             best_speaker = "Unknown"

#         formatted_line = f"[{start:.2f}s -> {end:.2f}s] [{best_speaker}]: {segment.text}"
#         final_transcript.append(formatted_line)
#         print(formatted_line)

#     with open(output_file, "w", encoding="utf-8") as f:
#         f.write("\n".join(final_transcript))
        
#     print(f"Transcript saved to {output_file}")

## Test code
# main():
#     input_file = get_config("input_file")
#     output_dir = get_config("output_dir")
#     output_file = generate_output_filename(input_file, output_dir)

#     transcribe_audio(
#         {
#             "input_file": input_file,
#             "output_file": output_file,
#         }
#     )
#     return 0


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
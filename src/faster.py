import os
from datetime import datetime
from faster_whisper import WhisperModel
from utils import get_config, load_key
from pyannote.audio import Pipeline
from pyannote.core import Annotation
# import torch


SUPPORTED_FORMATS = [".mp3", ".mp4", ".wav", ".m4a", ".mov", ".mkv", ".webm"]

model_whisper = get_config("model_whisper")
# print(model_whisper)

device = get_config("device")
# print(device)

model = WhisperModel(model_whisper, device=device, compute_type="int8")


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

# Whisper only
def transcribe_audio(input_file: str, output_file: str, beam_size: int = 5) -> None:
    """Transcribe audio file to text."""
    if not validate_audio_file(input_file):
        raise ValueError(
            f"Invalid audio file: {input_file}. "
            f"File must exist and have one of these extensions: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    segments, info = model.transcribe(input_file, beam_size=beam_size)
    
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    
    with open(output_file, "w") as f:
        for segment in segments:
            line = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
            
            print(line)
            
            f.write(line + "\n")
    
    print(f"Transcript saved to {output_file}")

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

# File path
input_file = get_config("input_file")
output_dir = get_config("output_dir")
output_file = generate_output_filename(input_file, output_dir)

transcribe_audio(input_file, output_file)
# transcribe_and_diarize(input_file, output_file)
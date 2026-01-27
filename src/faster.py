import os
from faster_whisper import WhisperModel

SUPPORTED_FORMATS = [".mp3", ".mp4", ".wav", ".m4a", ".mov", ".mkv", ".webm"]

model_size = "large-v2"
model = WhisperModel(model_size, device="cpu", compute_type="int8")


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


# File path
input_file = "../uploads/Recording.mp3"
output_dir = "../outputs"
output_file = os.path.join(output_dir, "transcript.txt")

transcribe_audio(input_file, output_file)
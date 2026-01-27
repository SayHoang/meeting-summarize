import os
from faster_whisper import WhisperModel

model_size = "large-v2"

model = WhisperModel(model_size, device="cpu", compute_type="int8")

# File path
input_file = "../uploads/Recording.mp3"
output_dir = "../outputs"
output_file = os.path.join(output_dir, "transcript.txt")

segments, info = model.transcribe(input_file, beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

with open(output_file, "w") as f:
    for segment in segments:
        line = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)

        print(line)

        f.write(line + "\n")

print(f"Transcript saved to {output_file}")
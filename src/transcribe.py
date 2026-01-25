import whisper

# Load model
model = whisper.load_model("medium", device="cpu")

# Result
result = model.transcribe("Recording.mp3")

segments = result["segments"]
info = result["language"]
info = result["language_probability"]

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment["start"], segment["end"], segment["text"]))
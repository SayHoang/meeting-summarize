import whisper

model = whisper.load_model("medium")
result = model.transcribe("audio.mp4")
print(result["text"])
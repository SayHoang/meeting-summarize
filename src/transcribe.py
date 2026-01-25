import whisper

model = whisper.load_model("small")
result = model.transcribe("audio.mp3", fp16=False)

# print(result)

print(result["text"])
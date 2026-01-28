import os
import torch
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

from dotenv import load_dotenv
load_dotenv()

# Community-1 open-source speaker diarization pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1",
    token=os.getenv("HF_TOKEN"))

# send pipeline to GPU (when available)
pipeline.to(torch.device("cpu"))

# apply pretrained pipeline (with optional progress hook)
with ProgressHook() as hook:
    output = pipeline("afjiv.wav", hook=hook)  # runs locally

# print the result
for turn, speaker in output.speaker_diarization:
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
# start=0.2s stop=1.5s speaker_0
# start=1.8s stop=3.9s speaker_1
# start=4.2s stop=5.7s speaker_0
# ...

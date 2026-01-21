# meeting-summarize

## 🛠️ Development

### Project Structure

```
meeting-assistant/
├── data/
│   ├── raw_audio/                # record meeting (.mp3, .wav)
│   ├── transcripts/              # transcript from Whisper (contain: .srt, .tsv, .txt, .vtt)
│   └── reports/                  # summarize from transcript
├── src/
│   ├── audio_processing/
│   │   ├── whisper.py            # Code Whisper
│   │   └── diarization.py        # Code seperate speakers
│   ├── llm_engine/
│   │   ├── prompts.py            # Contain Prompt (Dev, PM, QA)
│   │   └── generator.py          # Code call API (OpenAI/Claude/Gemini) for summarize
│   ├── evaluation/
│   │   ├── judge_prompts.py
│   │   └── scorer.py
│   └── utils/
│       └── file_handler.py       # Read/write file JSON/Text
├── .env
├── app.py
└── requirements.txt
```

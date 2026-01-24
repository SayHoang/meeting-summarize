# meeting-summarize

## Whisper

### Models

|  Size  | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~10x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~7x       |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~4x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |
| turbo  |   809 M    |        N/A         |      `turbo`       |     ~6 GB     |      ~8x       |

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

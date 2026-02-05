# meeting-summarize

## Installation

### Install Whisper

```
pip install git+https://github.com/openai/whisper.git
```

### Install ffmpeg

```
sudo apt update && sudo apt install ffmpeg
```

### Install setuptool-rust

```
pip install setuptools-rust
```

### Install pyannote.audio

```
pip install pyannote.audio
```


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

### Run requirement

```
pip install -r requirements.txt
```

### Streamlit Meeting UI

```
streamlit run frontend/app.py
```

### Project Structure

```
KLTN/
│
├── backend/
│   ├── core/           # Transcribe/summarize core
│   ├── storage.py      # Filesystem job storage
│   ├── paths.py        # Paths for storage
│   ├── types.py        # Pydantic types
│   ├── transcribe_service.py
│   └── summarize_service.py
│
├── frontend/
│   ├── app.py          # Streamlit UI
│   └── pages/          # History & Settings
│
├── meeting_storage/    # Stored jobs (audio/transcript/summary)


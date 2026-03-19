# meeting-summarize

## Installation

### Install faster-whisper

```bash
pip install -r requirements.txt
```

### Install ffmpeg (required for audio decoding)

```bash
sudo apt update && sudo apt install -y ffmpeg
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

## Configuration

### Environment Variables

Tạo file `.env` từ `.env.sample`:

```bash
cp .env.sample .env
```

Các biến tối thiểu để chạy đầy đủ:

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `N8N_WEBHOOK_URL`

### LLM Judge (criteria động)

Toàn bộ cấu hình Judge nằm trong `config.json`:

- `model_judge`
- `judge.enabled`
- `judge.scoring_mode`
- `judge.scale_min`, `judge.scale_max`
- `judge.criteria[]` (`name`, `display_name`, `direction`, `weight`)

Hướng dẫn chi tiết cách thêm tiêu chí mới (ví dụ `risk`), dùng weighted/simple average, và vị trí output report:

- [LLM Judge Configuration Guide](docs/llm_judge_guide.md)

## Run Locally

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start Streamlit (frontend + backend modules)

```bash
streamlit run frontend/app.py
```

Ứng dụng chạy tại: `http://localhost:8501`

## Run Full Stack with Docker Compose

Compose file chạy:

- Streamlit app (`frontend` + `backend` Python modules)
- n8n
- PostgreSQL cho n8n

### Start all services

```bash
docker compose up -d --build
```

### Service URLs

- Streamlit: `http://localhost:8501`
- n8n: `http://localhost:5678`
- PostgreSQL: `localhost:5432`

### Stop all services

```bash
docker compose down
```

## Project Structure (updated)

```text
kltn/
├── backend/
│   ├── api/
│   │   ├── summarize_service.py
│   │   ├── transcribe_service.py
│   │   ├── storage.py
│   │   └── types.py
│   └── core/
│       ├── summarize.py
│       ├── summarize_openai.py
│       └── judge.py
├── frontend/
│   └── app.py
├── docs/
│   └── llm_judge_guide.md
├── meeting_storage/
├── config.json
└── docker-compose.yml
```

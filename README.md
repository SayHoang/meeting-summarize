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

Hướng dẫn chi tiết cách thêm tiêu chí mới (ví dụ `Speed`), dùng weighted/simple average, và vị trí output report:

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

### Run n8n

```bash
docker compose up -d --build
```

### Import workflow into n8n
Check [Workflow](n8n_workflow/KLTN.json)

### Service URLs

|  Service      | Port                      |
|:-------------:|:-------------------------:|
|   Streamlit   | [http://localhost:8501](http://localhost:8501)     |
|   n8n         | [http://localhost:5678](http://localhost:5678)     |
|   PostgreSQL  | [http://localhost:5432](http://localhost:5432)     |

### Stop services

```bash
docker compose down
```

## Project Structure

```text
kltn/
├── backend/
│   ├── api/
│   │   ├── summarize_service.py
│   │   ├── transcribe_service.py
│   │   ├── storage.py
│   │   └── types.py
│   └── core/                       # Core app
|       ├── prompts/                # Folder chứa các câu prompt cho toàn bộ hệ thống
│       ├── faster.py               # Module chuyển đổi giọng nói thành văn bản
│       ├── summarize.py            # Module tóm tắt 1
│       ├── summarize_openai.py     # Module tóm tắt 2
│       └── judge.py                # Module judge
│       ├── param.json              # File chứa các thông số, setting của giao diện frontend/pages/settings.py
├── frontend/
│   ├── pages                       # Chứa các giao diện history, settings,...
│   └── app.py                      # Frontend chính thức
├── docs/
│   └── llm_judge_guide.md          # Tài liệu hướng dẫn setting LLM Judge
├── n8n_workflow/
│   └── KLTN.json                   # Template mẫu import workflow trong n8n
├── meeting_storage/
├── config.json
└── docker-compose.yml
```

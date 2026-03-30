# LLM Judge Configuration Guide

Tài liệu này hướng dẫn cách cấu hình LLM-as-a-Judge sau khi summarize, bao gồm:

- Thêm/bớt tiêu chí chấm.
- Chọn cách tính điểm tổng (`simple_average` hoặc `weighted_average`).
- Chọn hướng điểm cho từng tiêu chí (`higher_is_better` hoặc `lower_is_better`).
- Xem output report và vị trí lưu file.

## 1) Input ở đâu?

 Bạn chỉnh trực tiếp trong file `config.json`:

- `model_judge`: model Claude dùng để chấm.
- `judge`: block cấu hình toàn bộ logic chấm điểm.

Biến môi trường bắt buộc trong `.env`:

- `ANTHROPIC_API_KEY=...`

## 2) Cấu trúc cấu hình Judge

```json
{
  "model_judge": "anthropic-claude-3-5-sonnet-20240620",
  "judge": {
    "enabled": true,
    "provider": "anthropic",
    "scoring_mode": "simple_average",
    "scale_min": 1,
    "scale_max": 5,
    "criteria": [
      {
        "name": "accuracy",
        "display_name": "Accuracy",
        "direction": "higher_is_better"
      }
    ]
  }
}
```

Ý nghĩa:

- `enabled`: bật/tắt Judge.
- `provider`: hiện đang dùng `anthropic`.
- `scoring_mode`:
  - `simple_average`: trung bình cộng.
  - `weighted_average`: trung bình có trọng số.
- `scale_min` / `scale_max`: khoảng điểm mỗi tiêu chí (hiện dùng 1-5).
- `criteria`: danh sách tiêu chí động.

## 3) Thêm tiêu chí mới (ví dụ Risk)

### Option A - Trung bình cộng (simple average)

```json
{
  "judge": {
    "scoring_mode": "simple_average",
    "criteria": [
      { "name": "accuracy", "display_name": "Accuracy", "direction": "higher_is_better" },
      { "name": "completeness", "display_name": "Completeness", "direction": "higher_is_better" },
      { "name": "actionability", "display_name": "Actionability", "direction": "higher_is_better" },
      { "name": "risk", "display_name": "Risk", "direction": "lower_is_better" }
    ]
  }
}
```

Với điểm `risk=1, completeness=5, accuracy=4, actionability=3`:

- Điểm tổng = `(1 + 5 + 4 + 3) / 4 = 3.25`

### Option B - Trọng số (weighted average)

```json
{
  "judge": {
    "scoring_mode": "weighted_average",
    "criteria": [
      { "name": "accuracy", "display_name": "Accuracy", "direction": "higher_is_better", "weight": 40 },
      { "name": "completeness", "display_name": "Completeness", "direction": "higher_is_better", "weight": 30 },
      { "name": "actionability", "display_name": "Actionability", "direction": "higher_is_better", "weight": 20 },
      { "name": "risk", "display_name": "Risk", "direction": "lower_is_better", "weight": 10 }
    ]
  }
}
```

Ghi chú:

- Không bắt buộc tổng `weight = 100`; hệ thống tự chuẩn hóa theo tổng weight.
- Với tiêu chí `lower_is_better` (như `risk`), hệ thống sẽ đảo chiều nội bộ để tính tổng công bằng.

## 4) Output sau khi Judge chạy

Sau khi dual summarize xong:

- UI sẽ hiển thị:
  - recommendation (Summary 1 hoặc 2),
  - điểm từng tiêu chí,
  - tổng điểm,
  - ghi chú/rationale.
- Hệ thống **không auto-save** summary thắng; user vẫn bấm chọn thủ công.

File report được lưu tại:

- `meeting_storage/<job_id>/full_report.md`

Metadata cập nhật trong `meeting_storage/<job_id>/meta.json`:

- `judge_report_path`
- `judge_ready`

## 5) Các file đã implement Judge

- `backend/core/judge.py`: logic gọi Claude + parse score + tính tổng + render report markdown.
- `backend/api/summarize_service.py`: gọi judge sau khi có 2 summary.
- `backend/api/types.py`: mở rộng `DualSummaryResult`, `JobMeta`, thêm models cho judge.
- `backend/api/storage.py`: lưu `full_report.md`.
- `frontend/app.py`: hiển thị recommendation, score và full report.
- `config.json`: cấu hình judge.
- `config_notes.json`: mô tả ý nghĩa config.

## 6) Troubleshooting nhanh

- Thiếu key: kiểm tra `ANTHROPIC_API_KEY` trong `.env`.
- Judge không chạy: kiểm tra `judge.enabled=true`.
- Không thấy report: kiểm tra thư mục `meeting_storage/<job_id>/`.
- Điểm không như kỳ vọng: kiểm tra `direction` và `scoring_mode` trong `config.json`.

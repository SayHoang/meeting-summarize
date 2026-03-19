from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class JobMeta(BaseModel):
    job_id: str
    status: str = "created"
    created_at: datetime = Field(default_factory=_now_utc)
    updated_at: datetime = Field(default_factory=_now_utc)
    original_filename: Optional[str] = None
    input_path: Optional[str] = None
    transcript_path: Optional[str] = None
    summary_path: Optional[str] = None
    judge_report_path: Optional[str] = None
    transcript_ready: bool = False
    summary_ready: bool = False
    judge_ready: bool = False
    progress_transcribe: int = 0
    progress_summary: int = 0
    error_message: Optional[str] = None


class TranscribeParams(BaseModel):
    job_id: str
    input_path: str
    output_path: str
    beam_size: int = 5
    model_name: Optional[str] = None
    device: Optional[str] = None


class SummarizeParams(BaseModel):
    job_id: str
    transcript_path: str
    output_path: str
    prompt_text: Optional[str] = None
    model_name: Optional[str] = None


class JudgeCriterionScore(BaseModel):
    name: str
    display_name: str
    direction: str
    weight: float = 1.0
    summary_1_score: int
    summary_2_score: int
    summary_1_adjusted: float
    summary_2_adjusted: float
    reason: str = ""


class JudgeResult(BaseModel):
    enabled: bool = True
    provider: str
    model: str
    scoring_mode: str
    scale_min: int
    scale_max: int
    criteria: list[JudgeCriterionScore] = Field(default_factory=list)
    total_score_1: float
    total_score_2: float
    recommended_summary: Optional[int] = None
    overall_rationale: str = ""
    report_markdown: str = ""
    report_path: Optional[str] = None
    error_message: Optional[str] = None


class DualSummaryResult(BaseModel):
    summary_1: str
    summary_2: str
    model_1: Optional[str] = None
    model_2: Optional[str] = None
    judge_result: Optional[JudgeResult] = None


class ProgressEvent(BaseModel):
    stage: str
    percent: int
    message: str


class CreateTaskWebhookParams(BaseModel):
    summary_text: str
    job_id: Optional[str] = None
    webhook_url: Optional[str] = None
    timeout_seconds: float = 10.0


class CreateTaskWebhookResult(BaseModel):
    ok: bool
    status_code: int
    message: str
    raw_response: Optional[Any] = None

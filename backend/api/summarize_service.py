import sys
from pathlib import Path
from typing import Callable, Optional

from .paths import get_job_dir, get_prompt_override_path
from .storage import save_judge_report_markdown, update_meta
from .types import DualSummaryResult, SummarizeParams

_TEXT_ENCODING = "utf-8"


def _ensure_core_on_path() -> None:
    core_dir = Path(__file__).resolve().parents[1] / "core"
    if str(core_dir) not in sys.path:
        sys.path.append(str(core_dir))


def _load_prompt_override() -> Optional[str]:
    prompt_path = get_prompt_override_path()
    if prompt_path.exists():
        return prompt_path.read_text(encoding=_TEXT_ENCODING)
    return None


def run_summary(
    params: SummarizeParams,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    _ensure_core_on_path()
    from summarize import generate_summary_to_file

    job_dir = get_job_dir(params.job_id)
    prompt_text = params.prompt_text or _load_prompt_override()

    output_path = generate_summary_to_file(
        {
            "transcript_path": params.transcript_path,
            "output_file": params.output_path,
            "prompt_text": prompt_text,
            "model_name": params.model_name,
        },
        on_chunk=on_chunk,
    )

    update_meta(
        {
            "job_dir": job_dir,
            "updates": {
                "summary_path": output_path,
                "summary_ready": True,
            },
        }
    )
    return output_path


def run_dual_summary(params: SummarizeParams) -> DualSummaryResult:
    _ensure_core_on_path()
    from judge import run_judge
    from summarize import generate_summary_stream
    from summarize_openai import generate_summary_text
    from utils import get_config

    prompt_text = params.prompt_text or _load_prompt_override()
    model_1 = get_config("model_summary_1")
    model_2 = get_config("model_summary_2")

    summary_1 = "".join(
        generate_summary_stream(
            {
                "transcript_path": params.transcript_path,
                "prompt_text": prompt_text,
                "model_name": model_1,
            }
        )
    )

    summary_2 = generate_summary_text(
        {
            "transcript_path": params.transcript_path,
            "prompt_text": prompt_text,
            "model_name": model_2,
        }
    )

    judge_result = None
    try:
        judge_payload = run_judge(
            {
                "transcript_path": params.transcript_path,
                "summary_1": summary_1,
                "summary_2": summary_2,
                "model_1": model_1,
                "model_2": model_2,
            }
        )
        report_markdown = str(judge_payload.get("report_markdown") or "").strip()
        if report_markdown:
            report_path = save_judge_report_markdown(
                {"job_id": params.job_id, "report_markdown": report_markdown}
            )
            judge_payload["report_path"] = str(report_path)
        judge_result = judge_payload
    except Exception as exc:
        judge_result = {
            "enabled": False,
            "provider": "anthropic",
            "model": str(get_config("model_judge") or ""),
            "scoring_mode": "simple_average",
            "scale_min": 1,
            "scale_max": 5,
            "criteria": [],
            "total_score_1": 0.0,
            "total_score_2": 0.0,
            "recommended_summary": None,
            "overall_rationale": "",
            "report_markdown": "",
            "error_message": str(exc),
        }

    return DualSummaryResult(
        summary_1=summary_1,
        summary_2=summary_2,
        model_1=model_1,
        model_2=model_2,
        judge_result=judge_result,
    )

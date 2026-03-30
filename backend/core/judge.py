from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic
from openai import OpenAI
from utils import _load_transcript_text, load_key, read_config_file


def _default_criteria() -> list[dict[str, Any]]:
    return [
        {
            "name": "accuracy",
            "display_name": "Accuracy",
            "direction": "higher_is_better",
            "weight": 1.0,
        },
        {
            "name": "completeness",
            "display_name": "Completeness",
            "direction": "higher_is_better",
            "weight": 1.0,
        },
        {
            "name": "actionability",
            "display_name": "Actionability",
            "direction": "higher_is_better",
            "weight": 1.0,
        },
    ]


def _normalize_criterion(criterion: dict[str, Any], fallback_index: int) -> dict[str, Any]:
    name = str(criterion.get("name") or f"criterion_{fallback_index}").strip()
    if not name:
        name = f"criterion_{fallback_index}"

    display_name = str(criterion.get("display_name") or name.replace("_", " ").title())
    direction = str(criterion.get("direction") or "higher_is_better").strip().lower()
    if direction not in {"higher_is_better", "lower_is_better"}:
        direction = "higher_is_better"

    weight_value = criterion.get("weight", 1.0)
    try:
        weight = float(weight_value)
    except (TypeError, ValueError):
        weight = 1.0
    if weight <= 0:
        weight = 1.0

    return {
        "name": name,
        "display_name": display_name,
        "direction": direction,
        "weight": weight,
    }


def _load_judge_settings() -> dict[str, Any]:
    config = read_config_file()
    judge_config = config.get("judge") or {}
    scoring_mode = str(judge_config.get("scoring_mode") or "simple_average").strip().lower()
    if scoring_mode not in {"simple_average", "weighted_average"}:
        scoring_mode = "simple_average"

    scale_min = int(judge_config.get("scale_min", 1))
    scale_max = int(judge_config.get("scale_max", 5))
    if scale_min >= scale_max:
        scale_min, scale_max = 1, 5

    raw_criteria = judge_config.get("criteria")
    if not isinstance(raw_criteria, list) or not raw_criteria:
        raw_criteria = _default_criteria()

    normalized_criteria = [
        _normalize_criterion(item if isinstance(item, dict) else {}, idx + 1)
        for idx, item in enumerate(raw_criteria)
    ]

    return {
        "enabled": bool(judge_config.get("enabled", True)),
        "provider": str(judge_config.get("provider") or "anthropic").strip().lower(),
        "model": str(config.get("model_judge") or "anthropic-claude-3-5-sonnet-20240620"),
        "scoring_mode": scoring_mode,
        "scale_min": scale_min,
        "scale_max": scale_max,
        "criteria": normalized_criteria,
    }


def _extract_text_content(response: Any) -> str:
    chunks: list[str] = []
    for item in getattr(response, "content", []) or []:
        if getattr(item, "type", "") != "text":
            continue
        text_value = getattr(item, "text", "")
        if text_value:
            chunks.append(text_value)
    return "\n".join(chunks).strip()


def _extract_json_payload(content_text: str) -> dict[str, Any]:
    text = content_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        raise ValueError("Judge response does not contain a JSON object.")

    return json.loads(text[first_brace : last_brace + 1])


def _coerce_score(value: Any, scale_min: int, scale_max: int) -> int:
    try:
        numeric_value = int(round(float(value)))
    except (TypeError, ValueError):
        numeric_value = scale_min
    return max(scale_min, min(scale_max, numeric_value))


def _adjust_for_direction(score: int, direction: str, scale_min: int, scale_max: int) -> float:
    if direction == "lower_is_better":
        return float(scale_min + scale_max - score)
    return float(score)


def _build_judge_prompt(params: dict[str, Any]) -> str:
    criteria_text = "\n".join(
        [
            (
                f"- name: {criterion['name']}, display_name: {criterion['display_name']}, "
                f"direction: {criterion['direction']}"
            )
            for criterion in params["criteria"]
        ]
    )

    return (
        "You are a strict meeting-summary judge.\n"
        "Evaluate two summaries against the transcript.\n"
        "Use only the criteria provided.\n"
        f"Score range per criterion: {params['scale_min']}..{params['scale_max']}.\n"
        "Return ONLY a valid JSON object in this exact schema:\n"
        "{\n"
        '  "criteria": [\n'
        "    {\n"
        '      "name": "criterion_name",\n'
        '      "summary_1_score": 1,\n'
        '      "summary_2_score": 1,\n'
        '      "reason": "brief reason"\n'
        "    }\n"
        "  ],\n"
        '  "overall_rationale": "brief final rationale"\n'
        "}\n\n"
        f"Criteria:\n{criteria_text}\n\n"
        "Transcript:\n"
        f"{params['transcript_text']}\n\n"
        "Summary 1:\n"
        f"{params['summary_1']}\n\n"
        "Summary 2:\n"
        f"{params['summary_2']}\n"
    )


def _call_anthropic_judge(params: dict[str, Any]) -> dict[str, Any]:
    client = Anthropic(api_key=params["api_key"])
    response = client.messages.create(
        model=params["model"],
        max_tokens=1200,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": _build_judge_prompt(params),
            }
        ],
    )
    content_text = _extract_text_content(response)
    if not content_text:
        raise ValueError("Judge returned empty content.")
    return _extract_json_payload(content_text)


def _call_openrouter_judge(params: dict[str, Any]) -> dict[str, Any]:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=params["api_key"],
    )
    response = client.chat.completions.create(
        model=params["model"],
        messages=[
            {
                "role": "user",
                "content": _build_judge_prompt(params),
            }
        ],
        temperature=0,
    )
    if not response.choices:
        raise ValueError("OpenRouter judge returned no choices.")
    content_text = (response.choices[0].message.content or "").strip()
    if not content_text:
        raise ValueError("OpenRouter judge returned empty content.")
    return _extract_json_payload(content_text)


def _compute_totals(params: dict[str, Any]) -> tuple[float, float]:
    criteria = params["criteria"]
    scoring_mode = params["scoring_mode"]
    if not criteria:
        return 0.0, 0.0

    if scoring_mode == "weighted_average":
        total_weight = sum(item["weight"] for item in criteria)
        if total_weight <= 0:
            total_weight = float(len(criteria))
        total_1 = sum(item["summary_1_adjusted"] * item["weight"] for item in criteria) / total_weight
        total_2 = sum(item["summary_2_adjusted"] * item["weight"] for item in criteria) / total_weight
        return total_1, total_2

    total_1 = sum(item["summary_1_adjusted"] for item in criteria) / len(criteria)
    total_2 = sum(item["summary_2_adjusted"] for item in criteria) / len(criteria)
    return total_1, total_2


def _recommend_summary(total_score_1: float, total_score_2: float) -> int | None:
    if total_score_1 > total_score_2:
        return 1
    if total_score_2 > total_score_1:
        return 2
    return None


def _build_markdown_report(params: dict[str, Any]) -> str:
    lines = [
        "# LLM Judge Full Report",
        "",
        f"- Provider: `{params['provider']}`",
        f"- Model: `{params['model']}`",
        f"- Scoring mode: `{params['scoring_mode']}`",
        f"- Scale: `{params['scale_min']}..{params['scale_max']}`",
        "",
        "## Criteria Scores",
        "",
        "| Criterion | Direction | Summary 1 | Summary 2 | Note |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    has_lower_is_better = False
    for criterion in params["criteria"]:
        if criterion["direction"] == "lower_is_better":
            has_lower_is_better = True
        lines.append(
            "| "
            f"{criterion['display_name']} | "
            f"{criterion['direction']} | "
            f"{criterion['summary_1_score']} | "
            f"{criterion['summary_2_score']} | "
            f"{criterion['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- Summary 1 total: `{params['total_score_1']:.2f}`",
            f"- Summary 2 total: `{params['total_score_2']:.2f}`",
            (
                f"- Recommended summary: `Summary {params['recommended_summary']}`"
                if params["recommended_summary"] in {1, 2}
                else "- Recommended summary: `Tie / No strong winner`"
            ),
            "",
            "## Overall Rationale",
            "",
            params["overall_rationale"] or "No rationale returned.",
        ]
    )

    if has_lower_is_better:
        lines.extend(
            [
                "",
                "> Note: Criteria with `lower_is_better` are direction-normalized internally for total score calculation.",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def run_judge(params: dict[str, Any]) -> dict[str, Any]:
    settings = _load_judge_settings()
    if not settings["enabled"]:
        result = {
            "enabled": False,
            "provider": settings["provider"],
            "model": settings["model"],
            "scoring_mode": settings["scoring_mode"],
            "scale_min": settings["scale_min"],
            "scale_max": settings["scale_max"],
            "criteria": [],
            "total_score_1": 0.0,
            "total_score_2": 0.0,
            "recommended_summary": None,
            "overall_rationale": "",
            "report_markdown": "",
            "error_message": "Judge is disabled in config.",
        }
        return result

    provider = settings["provider"]
    api_key: str | None = None
    if provider == "anthropic":
        api_key = load_key("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for judge (provider=anthropic).")
    elif provider == "openrouter":
        api_key = load_key("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required for judge (provider=openrouter).")
    else:
        raise ValueError("Unsupported judge provider. Supported: anthropic, openrouter.")

    transcript_text = _load_transcript_text(params).strip()
    summary_1 = str(params.get("summary_1") or "").strip()
    summary_2 = str(params.get("summary_2") or "").strip()
    if not transcript_text:
        raise ValueError("Transcript is empty, cannot run judge.")
    if not summary_1 or not summary_2:
        raise ValueError("Both summary_1 and summary_2 are required.")

    call_params = {
        "api_key": api_key,
        "provider": provider,
        "model": settings["model"],
        "criteria": settings["criteria"],
        "scale_min": settings["scale_min"],
        "scale_max": settings["scale_max"],
        "transcript_text": transcript_text,
        "summary_1": summary_1,
        "summary_2": summary_2,
    }

    if provider == "anthropic":
        raw_result = _call_anthropic_judge(call_params)
    else:
        raw_result = _call_openrouter_judge(call_params)

    raw_criteria = raw_result.get("criteria")
    if not isinstance(raw_criteria, list):
        raise ValueError("Judge response missing criteria list.")

    criteria_by_name: dict[str, dict[str, Any]] = {}
    for item in raw_criteria:
        if not isinstance(item, dict):
            continue
        criterion_name = str(item.get("name") or "").strip()
        if criterion_name:
            criteria_by_name[criterion_name] = item

    normalized_results: list[dict[str, Any]] = []
    for criterion in settings["criteria"]:
        raw_item = criteria_by_name.get(criterion["name"], {})
        summary_1_score = _coerce_score(
            raw_item.get("summary_1_score"),
            settings["scale_min"],
            settings["scale_max"],
        )
        summary_2_score = _coerce_score(
            raw_item.get("summary_2_score"),
            settings["scale_min"],
            settings["scale_max"],
        )
        normalized_results.append(
            {
                "name": criterion["name"],
                "display_name": criterion["display_name"],
                "direction": criterion["direction"],
                "weight": criterion["weight"],
                "summary_1_score": summary_1_score,
                "summary_2_score": summary_2_score,
                "summary_1_adjusted": _adjust_for_direction(
                    summary_1_score,
                    criterion["direction"],
                    settings["scale_min"],
                    settings["scale_max"],
                ),
                "summary_2_adjusted": _adjust_for_direction(
                    summary_2_score,
                    criterion["direction"],
                    settings["scale_min"],
                    settings["scale_max"],
                ),
                "reason": str(raw_item.get("reason") or ""),
            }
        )

    total_score_1, total_score_2 = _compute_totals(
        {"criteria": normalized_results, "scoring_mode": settings["scoring_mode"]}
    )
    recommended_summary = _recommend_summary(total_score_1, total_score_2)

    result = {
        "enabled": True,
        "provider": settings["provider"],
        "model": settings["model"],
        "scoring_mode": settings["scoring_mode"],
        "scale_min": settings["scale_min"],
        "scale_max": settings["scale_max"],
        "criteria": normalized_results,
        "total_score_1": round(total_score_1, 4),
        "total_score_2": round(total_score_2, 4),
        "recommended_summary": recommended_summary,
        "overall_rationale": str(raw_result.get("overall_rationale") or ""),
    }
    result["report_markdown"] = _build_markdown_report(result)
    return result

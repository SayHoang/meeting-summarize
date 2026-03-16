from __future__ import annotations

from typing import Optional

from openai import OpenAI
from utils import get_config, load_key, load_prompt, _build_prompt, _load_transcript_text

def _load_default_prompt() -> str:
    return load_prompt("prompts/summary_prompt.txt")

def generate_summary_text(params: dict) -> str:
    api_key = load_key("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)
    model = params.get("model_name") or get_config("model_summary_2")
    prompt_text = params.get("prompt_text") or _load_default_prompt()
    transcript_text = _load_transcript_text(params)

    response = client.responses.create(
        model=model,
        input=_build_prompt(prompt_text, transcript_text),
        temperature=get_config("temperature_summary"),
        top_p=get_config("top_p_summary"),
    )

    if not getattr(response, "output", None):
        raise ValueError("OpenAI response missing output content.")

    first_output = response.output[0]
    parts = getattr(first_output, "content", []) or []
    texts = [
        getattr(part, "text", "")
        for part in parts
        if getattr(part, "text", None)
    ]
    if not texts:
        raise ValueError("OpenAI response output has no text parts.")

    return "".join(texts)


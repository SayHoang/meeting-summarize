from typing import Callable, Iterable, Optional

from google import genai
from utils import (
    get_config,
    load_key,
    load_prompt,
    _build_prompt,
    _load_transcript_text,
)

def _load_default_prompt() -> str:
    return load_prompt("prompts/summary_prompt.txt")

def generate_summary_stream(params: dict) -> Iterable[str]:
    """Generate summary stream for model 1."""
    api_key = load_key("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required.")

    client = genai.Client(api_key=api_key)
    model = params.get("model_name") or get_config("model_summary_1")
    prompt_text = params.get("prompt_text") or _load_default_prompt()
    transcript_text = _load_transcript_text(params)

    contents = [
        {
            "role": "user",
            "parts": [{"text": _build_prompt(prompt_text, transcript_text)}],
        }
    ]

    model_config = genai.types.GenerateContentConfig(
        temperature=get_config("temperature_summary"),
        top_p=get_config("top_p_summary"),
    )

    stream = client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=model_config,
    )

    for chunk in stream:
        text = getattr(chunk, "text", None)
        if text:
            yield text


def generate_summary_to_file(
    params: dict,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    output_file = params.get("output_file")
    if not output_file:
        raise ValueError("output_file is required.")

    with open(output_file, "w", encoding="utf-8") as f:
        for chunk_text in generate_summary_stream(params):
            f.write(chunk_text)
            if on_chunk:
                on_chunk(chunk_text)

    return output_file


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
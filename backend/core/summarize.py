import os
from datetime import datetime
from typing import Callable, Iterable, Optional

from google import genai
from utils import get_config, load_key, load_prompt

def generate_output_filename(input_file: str, output_dir: str) -> str:
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = f"summary_{timestamp}.txt"
    return os.path.join(output_dir, output_file)

def _build_prompt(prompt_text: str, transcript_text: str) -> str:
    return f"{prompt_text}:\n\n{transcript_text}"


def _load_default_prompt() -> str:
    return load_prompt("prompts/summary_prompt.txt")


def _load_transcript_text(params: dict) -> str:
    transcript_text = params.get("transcript_text")
    transcript_path = params.get("transcript_path")

    if transcript_text:
        return transcript_text

    if transcript_path:
        with open(transcript_path, "r") as f:
            return f.read()

    raise ValueError("transcript_text or transcript_path is required.")


def generate_summary_stream(params: dict) -> Iterable[str]:
    api_key = load_key("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required.")

    client = genai.Client(api_key=api_key)
    model = params.get("model_name") or get_config("model_summary")
    prompt_text = params.get("prompt_text") or _load_default_prompt()
    transcript_text = _load_transcript_text(params)

    contents = [
        {
            "role": "user",
            "parts": [{"text": _build_prompt(prompt_text, transcript_text)}],
        }
    ]

    for chunk in client.models.generate_content_stream(model=model, contents=contents):
        text = getattr(chunk, "text", "")
        if text:
            yield text


def generate_summary_to_file(
    params: dict,
    on_progress: Optional[Callable[[dict], None]] = None,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    output_file = params.get("output_file")
    if not output_file:
        raise ValueError("output_file is required.")

    chunk_index = 0
    with open(output_file, "w") as f:
        for chunk_text in generate_summary_stream(params):
            f.write(chunk_text)
            if on_chunk:
                on_chunk(chunk_text)

            if on_progress:
                chunk_index += 1
                percent = min(95, 5 + (chunk_index * 3))
                on_progress({"percent": percent, "message": "Summarizing..."})

    if on_progress:
        on_progress({"percent": 100, "message": "Summary completed"})

    return output_file

def main() -> int:
    transcript_path = "../outputs/ES2004c_20260127160026.txt"
    output_dir = get_config("output_dir")
    output_file = generate_output_filename(transcript_path, output_dir)

    generate_summary_to_file(
        {
            "transcript_path": transcript_path,
            "output_file": output_file,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
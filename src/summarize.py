from google import genai

from utils import load_prompt, get_config, load_key

def generate_summary(transcript: str, prompt_summary: str, model_summary: str) -> str:
    client = genai.Client(
        api_key=load_key("GEMINI_API_KEY")
    )

    model = model_summary
    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": f"{prompt_summary}: \n \n{transcript}"
                }
            ]
        }
    ]

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents
    ):
        print(chunk.text, end="", flush=True)

if __name__ == "__main__":
    file_path = "../outputs/ES2004c_20260127160026.txt"
    with open(file_path, "r") as f:
        transcript = f.read()

    prompt_summary = load_prompt("prompts/summary_prompt.txt")
    model_summary = get_config("model_summary")

    generate_summary(transcript, prompt_summary, model_summary)
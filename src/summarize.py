from google import genai
import os
from datetime import datetime
from utils import load_prompt, get_config, load_key

def generate_output_filename(input_file: str, output_file: str) -> str:
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = f"summary_{timestamp}.txt"
    return os.path.join(output_dir, output_file)

def generate_summary(transcript: str, output_file: str) -> str:
    client = genai.Client(
        api_key=load_key("GEMINI_API_KEY")
    )

    model = get_config("model_summary")
    prompt_summary = load_prompt("prompts/summary_prompt.txt")

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

    with open(output_file, "w") as f:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents
        ):
            f.write(chunk.text)
            # print(chunk.text, end="", flush=True)

    print(f"Summary saved to {output_file}")

if __name__ == "__main__":
    file_path = "../outputs/ES2004c_20260127160026.txt"
    with open(file_path, "r") as f:
        transcript = f.read()

    output_dir = get_config("output_dir")
    output_file = generate_output_filename(file_path, output_dir)

    generate_summary(transcript, output_file)
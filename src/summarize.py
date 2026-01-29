from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

file_path = "../outputs/ES2004c_20260127160026.txt"

with open(file_path, "r") as f:
    transcript = f.read()

# print(transcript)
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=f"Summarize this transcript: \n \n{transcript}"
)

print(response.text)
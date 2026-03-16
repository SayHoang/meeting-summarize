from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

stream = client.responses.create(
    model="gpt-4.1-mini",
    input=[
        {
            "role": "user",
            "content": "say 'hello' 3 times",
        },
    ],
    stream=True,
)

for event in stream:
    print(event)
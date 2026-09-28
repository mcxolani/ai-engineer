from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

model = "text-embedding-3-small"
text = "I cannot sign in to my account."

with OpenAI(timeout=20.0, max_retries=0) as client:
    response = client.embeddings.create(
        model=model,
        input=text,
        encoding_format="float",
    )

vector = response.data[0].embedding

print(f"Model: {response.model}")
print(f"Text: {text}")
print(f"Dimensions: {len(vector)}")
print(f"First five numbers: {vector[:5]}")
print(f"Input tokens: {response.usage.prompt_tokens}")

from math import sqrt
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def cosine_similarity(left, right):
    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_length = sqrt(sum(value * value for value in left))
    right_length = sqrt(sum(value * value for value in right))
    return dot_product / (left_length * right_length)


load_dotenv(Path(__file__).resolve().parent / ".env")

texts = ["login", "sign in", "banana"]

with OpenAI(timeout=20.0, max_retries=0) as client:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        encoding_format="float",
    )

vectors = {item.index: item.embedding for item in response.data}
login = vectors[0]
sign_in = vectors[1]
banana = vectors[2]

print(f"Vectors returned: {len(vectors)}")
print(f"login / login: {cosine_similarity(login, login):.4f}")
print(f"login / sign in: {cosine_similarity(login, sign_in):.4f}")
print(f"login / banana: {cosine_similarity(login, banana):.4f}")
print(f"Input tokens: {response.usage.prompt_tokens}")

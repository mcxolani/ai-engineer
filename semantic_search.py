from math import sqrt
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from search_document import chunks


def cosine_similarity(left, right):
    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_length = sqrt(sum(value * value for value in left))
    right_length = sqrt(sum(value * value for value in right))
    return dot_product / (left_length * right_length)


load_dotenv(Path(__file__).resolve().parent / ".env")

query = input("Search: ").strip()
if not query:
    raise SystemExit("Enter a search before requesting embeddings.")

texts = [query] + [chunk["text"] for chunk in chunks]

with OpenAI(timeout=20.0, max_retries=0) as client:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        encoding_format="float",
    )

vectors = {item.index: item.embedding for item in response.data}
query_vector = vectors[0]

ranked = []
for index, chunk in enumerate(chunks, start=1):
    score = cosine_similarity(query_vector, vectors[index])
    ranked.append((score, chunk))

ranked.sort(key=lambda result: result[0], reverse=True)

print(f"Vectors returned: {len(vectors)}")
for score, chunk in ranked:
    print(f"Chunk {chunk['id']}: {score:.4f} | {chunk['source']}")

best_score, best_chunk = ranked[0]
print(f"\nTop chunk: {best_chunk['id']}")
print(f"Source: {best_chunk['source']}")
print(best_chunk["text"])
print(f"Input tokens: {response.usage.prompt_tokens}")

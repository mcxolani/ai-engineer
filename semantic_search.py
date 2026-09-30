import json
from math import sqrt
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

MINIMUM_SCORE = 0.30


def cosine_similarity(left, right):
    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_length = sqrt(sum(value * value for value in left))
    right_length = sqrt(sum(value * value for value in right))
    return dot_product / (left_length * right_length)


def find_chunk(query):
    query = query.strip()
    if not query:
        raise ValueError("Enter a search before requesting embeddings.")

    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    index_path = root / "data" / "embeddings.json"
    if not index_path.exists():
        raise FileNotFoundError("Run python build_index.py first.")

    saved = json.loads(index_path.read_text(encoding="utf-8"))
    chunks = saved["chunks"]
    if not chunks:
        raise ValueError("The saved file has no chunks. Rebuild it first.")

    with OpenAI(timeout=20.0, max_retries=0) as client:
        response = client.embeddings.create(
            model=saved["model"],
            input=query,
            encoding_format="float",
        )

    query_vector = response.data[0].embedding
    ranked = []
    for chunk in chunks:
        score = cosine_similarity(query_vector, chunk["embedding"])
        ranked.append((score, chunk))
    ranked.sort(key=lambda result: result[0], reverse=True)

    best_score, best_chunk = ranked[0]
    accepted_chunk = best_chunk if best_score >= MINIMUM_SCORE else None
    return accepted_chunk, best_score, response.usage.prompt_tokens


if __name__ == "__main__":
    chunk, score, tokens = find_chunk(input("Search: "))
    print(f"Top score: {score:.4f}")
    print(f"Minimum score: {MINIMUM_SCORE:.2f}")
    if chunk is None:
        print("Result: no match above the minimum score.")
    else:
        print(f"Result: accepted chunk {chunk['id']}")
        print(f"Source: {chunk['source']}")
        print(chunk["text"])
    print(f"Input tokens: {tokens}")

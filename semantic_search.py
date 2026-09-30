import json
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

query = input("Search: ").strip()
if not query:
    raise SystemExit("Enter a search before requesting embeddings.")

# texts = [query] + [chunk["text"] for chunk in chunks]

# with OpenAI(timeout=20.0, max_retries=0) as client:
#     response = client.embeddings.create(
#         model="text-embedding-3-small",
#         input=texts,
#         encoding_format="float",
#     )

# vectors = {item.index: item.embedding for item in response.data}
# query_vector = vectors[0]

# ranked = []
# for index, chunk in enumerate(chunks, start=1):
#     score = cosine_similarity(query_vector, vectors[index])
#     ranked.append((score, chunk))

# ranked.sort(key=lambda result: result[0], reverse=True)

# print(f"Vectors returned: {len(vectors)}")

index_path = Path(__file__).resolve().parent / "data" / "embeddings.json"
if not index_path.exists():
    raise SystemExit("Run python build_index.py first.")

saved = json.loads(index_path.read_text(encoding="utf-8"))
chunks = saved["chunks"]
if not chunks:
    raise SystemExit("The saved file has no chunks. Rebuild it first.")

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

print(f"Saved chunks loaded: {len(chunks)}")
print(f"Vectors returned for query: {len(response.data)}")

for score, chunk in ranked:
    print(f"Chunk {chunk['id']}: {score:.4f} | {chunk['source']}")

minimum_score = 0.30
best_score, best_chunk = ranked[0]

print(f"\nTop candidate: {best_chunk['id']}")
print(f"Top score: {best_score:.4f}")
print(f"Minimum score: {minimum_score:.2f}")

if best_score >= minimum_score:
    print(f"Result: accepted chunk {best_chunk['id']}")
    print(f"Source: {best_chunk['source']}")
    print(best_chunk["text"])
else:
    print("Result: no match above the minimum score.")

print(f"Input tokens: {response.usage.prompt_tokens}")

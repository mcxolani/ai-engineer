# Day 21: search your document with embeddings

Allow 20–25 minutes. Today you will combine your document chunks with the
similarity calculation from Day 20.

The steps are: embed the question and chunks, compare each chunk with the
question, then sort by score. This follows the approach in the
[official text search example](https://developers.openai.com/api/docs/guides/embeddings#text-search-using-embeddings).

## 1. Create the search script

Create `semantic_search.py` in the project root:

```python
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
```

The import reuses the chunks from Day 18's `search_document.py`. Its main guard
prevents the keyword search prompt from running during import.

We repeat the small cosine function here. Importing `compare_embeddings.py`
as currently written would also run its API request.

Index 0 holds the query's vector; indices 1–3 hold the chunk vectors in document
order. `ranked.sort(...)` puts the highest score first while keeping each score
with its chunk and source filename.

## 2. Search for login

Use your existing `.env` and run:

```bash
source .venv/bin/activate
python semantic_search.py
```

Enter `login`. Expect four vectors: one for the query and three for the chunks.
We expect chunk 3 to rank first because it contains the account access guidance.
Read the returned text and report your actual result and score.

Compare this with Day 18: the keyword search returned `None` for `login`.
The embedding search can compare related wording without requiring that exact
word to appear in the chunk.

Each run makes one paid embeddings request with the query and all three chunks;
automatic retries are disabled. The script regenerates the document vectors
on every run. We will save and reuse them in a later lesson.

## 3. Try an unrelated query

Run the script once more and enter `banana`.

It will still return a top chunk. That is how this code works: it ranks every
chunk and selects the first, even when none addresses the query. There is no
particular chunk that must win for `banana`.

Read its text. Does it contain information about bananas? This is the limitation
to notice: ranking finds the closest available chunk, but we still need a way
to handle queries that the document cannot answer.

Keep the existing five-case keyword evaluation as your baseline. We have not
yet measured the embedding search on all five cases or added a no-match rule.

## Done when

Send:

```text
Vectors returned for login: __
Top chunk for login: __
Top score for login: __
Source: __
Top chunk for banana: __
Does that chunk answer banana: yes/no
Why does banana still get a result: __
```

# Day 24: evaluate the embedding search

Allow 25–30 minutes. Today you will score the embedding search using the same
five examples from Day 18. The keyword search scored 4/5 because `login` failed.

## 1. Make search reusable

Replace `semantic_search.py` with the following version. It moves the existing
search into a function, just as you did with keyword search in Day 18.

```python
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
```

The function returns three values: the accepted chunk (or `None`), the highest
similarity score, and the query's input token count. It loads the saved file
each time, but does not regenerate the document embeddings.

The main guard keeps the prompt out of imports. Check that importing makes no
request and asks for no input:

```bash
source .venv/bin/activate
python -c "import semantic_search; print('Import ready')"
```

Interactive search still works with `python semantic_search.py`. You can use
the automated evaluation below for today's live checks.

## 2. Create the evaluation

Create `evaluate_semantic.py` beside `evaluate_retrieval.py`:

```python
from semantic_search import MINIMUM_SCORE, find_chunk

cases = [
    ("password reset", 3),
    ("duplicate payment", 2),
    ("support hours", 1),
    ("banana", None),
    ("login", 3),
]

passed = 0
total_tokens = 0
print(f"Minimum score: {MINIMUM_SCORE:.2f}")

for query, expected_id in cases:
    chunk, similarity, tokens = find_chunk(query)
    actual_id = chunk["id"] if chunk is not None else None
    total_tokens += tokens
    correct = actual_id == expected_id
    if correct:
        passed += 1

    status = "PASS" if correct else "FAIL"
    print(f"{query}: {status} | expected={expected_id}, actual={actual_id}")
    print(f"  Similarity: {similarity:.4f} | Input tokens: {tokens}")

print(f"Score: {passed}/{len(cases)}")
print(f"Total query input tokens: {total_tokens}")
```

Run:

```bash
python evaluate_semantic.py
```

This makes five paid embeddings requests, one for each query, with retries
disabled. It reuses your existing saved file. The reported total excludes the
earlier cost of building the document embeddings.

If an API or file error stops the script, resolve it before reporting a complete
score. An error is different from a successful search returning `None`.

## 3. Compare the results

Keep the original `evaluate_retrieval.py` as the keyword baseline. Compare its
recorded 4/5 with the new score. Check both whether `login` now passes and whether
`banana` still returns no match. Report any failures with their similarity scores;
keep the minimum at 0.30 for this run.

A result of 5/5 means these five checks passed. They are familiar development
examples, including queries used while choosing the cutoff, so this does not
establish accuracy on new questions. We will need a broader set of examples.
Automated, task-specific checks are also recommended in the
[official evaluation guide](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

## Done when

Send:

```text
Import without prompt: yes/no
Embedding search score: __/5
login result: __
banana result: __
Total query input tokens: __
Failed queries, if any: __
Why does 5/5 not prove every future search will work: __
```

Completed: import reported safe; embedding retrieval scored 5/5 with 8 query
input tokens and no failures. `login` returned chunk 3 and `banana` returned
`None`. Correctly identified the small dataset as a limitation; these examples
also guided development, so new questions still need evaluation.

Next: [Day 25 — answer from a retrieved passage](day-25.md).

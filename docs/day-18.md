# Day 18: score your search results

Allow 20–25 minutes. Today you will automatically check which chunk your search
returns. This is similar to the ticket evaluation you built in Project 1.
Everything runs locally, with no API calls or database.

## 1. Make the search reusable

In `search_document.py`, keep everything above `query = input(...)`.
Replace that line and everything below it with:

```python
def find_chunk(query):
    query_words = words(query)
    best_chunk = None
    best_score = 0

    for chunk in chunks:
        score = len(query_words & words(chunk["text"]))
        if score > best_score:
            best_chunk = chunk
            best_score = score

    return best_chunk, best_score


if __name__ == "__main__":
    query = input("Search keywords: ")
    best_chunk, best_score = find_chunk(query)

    if best_chunk is None:
        print("No matching chunk found.")
    else:
        print(f"Source: {best_chunk['source']}")
        print(f"Chunk: {best_chunk['id']}")
        print(f"Matching words: {best_score}")
        print(best_chunk["text"])
```

The function returns the selected chunk and its word-overlap score.
The `if __name__ == "__main__":` line runs the interactive prompt only when
you run this file directly. Another script can now import `find_chunk` without
being asked to type a search. The document still loads when the module is imported.

Run `python search_document.py` and try `password reset` once to check that
interactive search still works.

## 2. Run five examples automatically

Create `evaluate_retrieval.py` beside `search_document.py`:

```python
from search_document import find_chunk

cases = [
    ("password reset", 3),
    ("duplicate payment", 2),
    ("support hours", 1),
    ("banana", None),
    ("login", 3),
]

passed = 0
for query, expected_id in cases:
    chunk, _ = find_chunk(query)
    actual_id = chunk["id"] if chunk is not None else None
    correct = actual_id == expected_id
    if correct:
        passed += 1

    status = "PASS" if correct else "FAIL"
    print(f"{query}: {status} | expected={expected_id}, actual={actual_id}")

print(f"Score: {passed}/{len(cases)}")
```

Each example pairs a search with the result we want. `None` means there should
be no match. The `_` receives the overlap score, which this evaluation does not
use: it checks whether the selected chunk is the right one.

From the project root, run:

```bash
source .venv/bin/activate
python evaluate_retrieval.py
```

## 3. Explain the failure

With the unchanged sample document and keyword search, expect **4/5**.
The `login` example should show `expected=3, actual=None`.

Chunk 3 has relevant sign-in guidance, so 3 is the desired result even though
our current search cannot find it using `login`. Keep that expected result:
the failure records a limitation we can measure when we improve retrieval.

These five familiar examples are a development check. A higher score here
would not establish that the search handles every new question correctly.

## Done when

Send:

```text
Interactive search still works: yes/no
Score: __/5
Failed query: __
Expected chunk / actual chunk: __ / __
Why it failed: __
```

Completed: interactive search reported working; evaluation scored 4/5.
The failed query was `login`, with expected chunk 3 and actual result `None`.
The search compares whole words: `login` does not match `sign` or `in`.

Next: [Day 19 — create your first embedding](day-19.md).

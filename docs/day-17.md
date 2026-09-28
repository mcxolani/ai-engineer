# Day 17: find a chunk with keywords

Allow 15–20 minutes. Yesterday you selected a relevant chunk yourself.
Today Python will select one by counting matching words. This is a simple
first version of **retrieval**: finding text that may help answer a question.

Everything runs locally. No API or database is needed.

## 1. Create the search script

Create `search_document.py` beside `chunk_document.py`. The first part repeats
the document loading you already know; the new part scores each chunk.

```python
import re
from pathlib import Path


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


source = Path(__file__).resolve().parent / "documents" / "sample-policy.txt"
text = source.read_text(encoding="utf-8")
paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
chunks = [
    {"id": number, "source": source.name, "text": paragraph}
    for number, paragraph in enumerate(paragraphs, start=1)
]

query = input("Search keywords: ")
query_words = words(query)
best_chunk = None
best_score = 0

for chunk in chunks:
    score = len(query_words & words(chunk["text"]))
    if score > best_score:
        best_chunk = chunk
        best_score = score

if best_chunk is None:
    print("No matching chunk found.")
else:
    print(f"Source: {best_chunk['source']}")
    print(f"Chunk: {best_chunk['id']}")
    print(f"Matching words: {best_score}")
    print(best_chunk["text"])
```

`words()` lowercases the text and extracts English words, ignoring punctuation.
`set` keeps each word only once. The `&` finds words shared by the search and
the chunk, so `len(...)` gives the number of distinct matching words.

The chunk with the highest score wins. If scores tie, this loop keeps the first
matching chunk. If every score is zero, it reports no match.

## 2. Try four searches

Run this command once for each search below:

```bash
source .venv/bin/activate
python search_document.py
```

| Enter these keywords | Expected result |
| --- | --- |
| `password reset` | Chunk 3, score 2 |
| `duplicate payment` | Chunk 2, score 2 |
| `support hours` | Chunk 1, score 2 |
| `banana` | No matching chunk found |

Read the selected text as well as the number. You should still see the filename
beside the chunk, so you can trace the result back to the document.

## 3. See one limitation

Try `login`. It returns no match even though chunk 3 discusses signing in.
Our code matches exact words; it does not know that these phrases are related.
Likewise, `payment` and `payments` are different words to this function.

Use short keywords for now. Common words in a full question can produce an
unhelpful match. A positive score measures word overlap, not answer correctness.

## Done when

Send your results:

```text
password reset → chunk: __
duplicate payment → chunk: __
support hours → chunk: __
banana → result: __
Why does login find no match: __
```

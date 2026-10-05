# Day 34 — answer questions from two documents

Today you will add a second text file and reuse your existing embedding,
import, search, and answer pipeline. Allow 30–40 minutes.

The complete exercise uses one batch embedding request to rebuild the cache,
six query embeddings for evaluation, and two manual questions (each with an
embedding and a generation request). That is **11 paid requests** in total.

## 1. Add another small document

Create `documents/remote-work-policy.txt` containing this single paragraph:

```text
Remote work: Employees at the fictional ExampleCo may work remotely for up to two days per week, with approval from their manager.
```

This is fictional practice content, just like `sample-policy.txt`.
You now have two files: the original three paragraphs and one new paragraph.

## 2. Load all the text files

Create `document_loader.py` in the project root:

```python
import re
from pathlib import Path


def load_chunks(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError("The document folder does not exist.")

    chunks = []
    for source in sorted(folder.glob("*.txt")):
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        for number, paragraph in enumerate(paragraphs, start=1):
            chunks.append({"id": number, "source": source.name, "text": paragraph})
    return chunks


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent / "documents"
    chunks = load_chunks(folder)
    for chunk in chunks:
        print(f"{chunk['source']} / chunk {chunk['id']}")
    print(f"Total chunks: {len(chunks)}")
```

`glob("*.txt")` selects text files directly inside the folder. Sorting makes
the file order repeatable. See [Python's pathlib documentation](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.glob).
The loader splits on blank lines and starts chunk numbering at 1 for each file.

Run from the project root:

```bash
source .venv/bin/activate
python document_loader.py
```

Expect:

```text
remote-work-policy.txt / chunk 1
sample-policy.txt / chunk 1
sample-policy.txt / chunk 2
sample-policy.txt / chunk 3
Total chunks: 4
```

Both files have a chunk 1. The pair `(source, chunk_id)` identifies which one
you mean, just as it does in the database primary key.

## 3. Rebuild the cache and import it

In `build_index.py`, replace:

```python
from search_document import chunks
```

with:

```python
from document_loader import load_chunks
```

Immediately after `root = Path(__file__).resolve().parent`, add:

```python
chunks = load_chunks(root / "documents")
```

Run:

```bash
docker compose -f compose.knowledge.yml up -d --wait vector-db
python build_index.py
python import_embeddings.py
```

Expect **4 saved chunks**, **1,536 dimensions**, and **4 imported chunks**.
The builder re-embeds all four paragraphs in one batch, including the original
three. The importer updates those three rows and inserts the new source/chunk pair.

Check the database:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT source, count(*) AS chunks FROM document_chunks GROUP BY source ORDER BY source;"
```

Expect `remote-work-policy.txt: 1` and `sample-policy.txt: 3`.
This exercise only adds a file. As before, the importer does not remove rows
for deleted documents or removed paragraphs.

## 4. Evaluate the source as well as the chunk number

Replace `evaluate_postgres.py` with:

```python
from pgvector_search import MINIMUM_SCORE, find_chunk

cases = [
    ("password reset", ("sample-policy.txt", 3)),
    ("duplicate payment", ("sample-policy.txt", 2)),
    ("support hours", ("sample-policy.txt", 1)),
    ("banana", None),
    ("login", ("sample-policy.txt", 3)),
    ("How many days per week can employees work remotely?", ("remote-work-policy.txt", 1)),
]

passed = 0
total_tokens = 0
print(f"Minimum score: {MINIMUM_SCORE:.2f}")

for query, expected in cases:
    chunk, similarity, tokens = find_chunk(query)
    actual = (chunk["source"], chunk["id"]) if chunk is not None else None
    total_tokens += tokens
    correct = actual == expected
    if correct:
        passed += 1

    status = "PASS" if correct else "FAIL"
    print(f"{query}: {status} | expected={expected}, actual={actual}")
    print(f"  Similarity: {similarity:.4f} | Input tokens: {tokens}")

print(f"Score: {passed}/{len(cases)}")
print(f"Total query input tokens: {total_tokens}")
```

Run:

```bash
python evaluate_postgres.py
ruff check document_loader.py build_index.py evaluate_postgres.py
```

Aim for **6/6** and passing lint. Report any failures with their source, chunk,
and score. Adding a document can change which chunk wins, including for old
queries, so keep the original cases. Keep the `0.30` threshold for this check.

## 5. Ask the API about both documents

Start the API if needed with
`uvicorn knowledge_api:app --host 127.0.0.1 --port 8001 --reload`.

At <http://127.0.0.1:8001/docs>, send this to `POST /ask`:

```json
{"question": "How many days per week can employees work remotely?"}
```

Expect 200, source `remote-work-policy.txt`, chunk 1, and completed generation.
The answer should say **up to two days per week, with manager approval**.
Check it against the paragraph; source metadata alone does not prove accuracy.

Then ask:

```json
{"question": "On which days and at what times is support available?"}
```

Expect the supported hours answer from `sample-policy.txt`, chunk 1.
Both responses have chunk 1, but different source filenames.

## Done when

Send:

```text
Files loaded / total chunks: __ / __
Database chunks per source: __
Retrieval score: __ / 6
Lint: pass/fail
Remote-work status / source / chunk: __ / __ / __
Remote-work answer supported by the passage: yes/no
Hours source / chunk: __ / __
Failed queries, if any: __
Why is checking only the chunk number no longer enough: __
```

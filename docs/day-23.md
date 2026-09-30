# Day 23: save and reuse document embeddings

Allow 25–30 minutes. Your current search embeds all three document chunks on
every run. Today you will save those vectors once and reuse them.

| Step | Text sent for embedding |
| --- | --- |
| Build the saved file | Three document chunks |
| Each search afterward | Only the query |

Embeddings can be saved and loaded for later use; see the
[official embeddings guide](https://developers.openai.com/api/docs/guides/embeddings#obtaining-the-embeddings).
We will use a JSON file for this small document.

## 1. Save the document vectors

Create `build_index.py` in the project root:

```python
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from search_document import chunks

root = Path(__file__).resolve().parent
load_dotenv(root / ".env")
model = "text-embedding-3-small"

if not chunks:
    raise SystemExit("The document has no chunks to embed.")

with OpenAI(timeout=20.0, max_retries=0) as client:
    response = client.embeddings.create(
        model=model,
        input=[chunk["text"] for chunk in chunks],
        encoding_format="float",
    )

vectors = {item.index: item.embedding for item in response.data}
saved_chunks = [
    {**chunk, "embedding": vectors[index]}
    for index, chunk in enumerate(chunks)
]
saved = {"model": model, "chunks": saved_chunks}

output = root / "data" / "embeddings.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(saved), encoding="utf-8")

print(f"Saved chunks: {len(saved_chunks)}")
print(f"Dimensions per chunk: {len(saved_chunks[0]['embedding'])}")
print(f"File: {output.relative_to(root)}")
print(f"Build input tokens: {response.usage.prompt_tokens}")
```

`{**chunk, "embedding": ...}` copies the chunk's ID, source, and text, then adds
its vector. Saving the model name lets search use the same model for the query.

Add this line to `.gitignore` for the generated file:

```gitignore
/data/embeddings.json
```

Run once:

```bash
source .venv/bin/activate
python build_index.py
```

Expect three saved chunks, each with 1,536 dimensions. This makes one paid
request. Rerunning the build makes another request and replaces the saved file.

## 2. Make search read the saved file

In `semantic_search.py`:

1. Add `import json` above `from math import sqrt`.
2. Remove `from search_document import chunks`.
3. Replace the block starting at `texts = [query] + ...` and ending with
   `print(f"Vectors returned: {len(vectors)}")` with the following:

```python
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
```

Keep the existing cosine function, query prompt, ranking display, and 0.30
minimum-score rule. The `Input tokens` printed by search now counts only the
query, because the document vectors came from the file.

## 3. Verify reuse

Run `python semantic_search.py` and enter `login`. Expect three saved chunks
loaded, one new query vector, and accepted chunk 3.

After that process finishes, run it again and enter `banana`, without rebuilding.
Expect the same saved chunks to load and the final result to be no match.

The exercise makes three paid requests in total: one build and two searches.
Both searches still call the API for their query; loading and comparing saved
document vectors happens locally.

The saved file is a snapshot. If you edit the document or its chunking, run
`build_index.py` again before searching. To change the embedding model, change
it in the build script and rebuild. Search uses the saved model name. This
simple version does not automatically detect changes to the original document.

## Done when

Send:

```text
Saved chunks: __
Dimensions per chunk: __
Saved chunks loaded during search: __
Vectors returned for query: __
login result: __
banana result after restarting the script: __
Why does search use fewer input tokens now: __
```

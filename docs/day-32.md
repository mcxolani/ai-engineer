# Day 32 — search your vectors in PostgreSQL

Today you will ask PostgreSQL to find the closest stored chunk to a question.
Allow 25–30 minutes.

The flow is: question → query embedding → SQL similarity search → accepted chunk
or no match. This lesson uses paid embeddings for the questions, with no answer
generation. Following the examples once uses **seven embedding requests**.

## 1. Create the database search

Create `pgvector_search.py` in the project root:

```python
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from psycopg.rows import dict_row

EMBEDDING_MODEL = "text-embedding-3-small"
MINIMUM_SCORE = 0.30


def find_chunk(query):
    query = query.strip()
    if not query:
        raise ValueError("Enter a search before requesting embeddings.")

    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    database_url = os.getenv("KNOWLEDGE_DATABASE_URL")
    if not database_url:
        raise RuntimeError("Set KNOWLEDGE_DATABASE_URL in .env first.")

    with psycopg.connect(
        database_url, connect_timeout=5, row_factory=dict_row, autocommit=True
    ) as connection:
        existing = connection.execute(
            "SELECT 1 FROM document_chunks WHERE embedding_model = %s LIMIT 1",
            (EMBEDDING_MODEL,),
        ).fetchone()
        if existing is None:
            raise RuntimeError("Import chunks for this embedding model first.")

        with OpenAI(timeout=20.0, max_retries=0) as client:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=query,
                encoding_format="float",
            )

        vector = json.dumps(response.data[0].embedding, allow_nan=False)
        row = connection.execute(
            """
            SELECT source, chunk_id, content,
                   1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE embedding_model = %s
            ORDER BY embedding <=> %s::vector, source, chunk_id
            LIMIT 1
            """,
            (vector, EMBEDDING_MODEL, vector),
        ).fetchone()

    if row is None:
        raise RuntimeError("No chunks remain for this embedding model.")

    score = float(row["score"])
    chunk = {
        "id": row["chunk_id"],
        "source": row["source"],
        "text": row["content"],
    }
    accepted_chunk = chunk if score >= MINIMUM_SCORE else None
    return accepted_chunk, score, response.usage.prompt_tokens


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

The embedding call uses the same model as your saved vectors. It sends only
the question, following the
[official OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings).

Read the SQL in four steps:

1. `WHERE embedding_model = %s` selects vectors from the same model.
2. `<=>` calculates cosine distance. `ORDER BY` defaults to ascending, so the
   smallest distance comes first. Source and chunk number settle any exact ties.
3. `LIMIT 1` returns the closest row.
4. `1 - distance` gives the similarity score used by your `0.30` threshold.

PostgreSQL performs the comparisons and returns one row to Python. With this
table, the search is exact; we have not added an approximate vector index.
See the [pgvector query guide](https://github.com/pgvector/pgvector#querying).

`dict_row` lets you access fields by name, such as `row["content"]`.
`autocommit=True` keeps these separate reads from leaving a transaction open
while the embedding request runs. The database connection closes when its
`with` block ends. See [Psycopg row factories](https://www.psycopg.org/psycopg3/docs/advanced/rows.html)
and [transaction handling](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

An empty table or missing matching model raises an error before requesting an
embedding. A populated table whose best score is too low returns a normal
no-match result. Those are different situations.

## 2. Try two searches

From the project root:

```bash
source .venv/bin/activate
docker compose -f compose.knowledge.yml up -d --wait vector-db
python -c "import pgvector_search; print('Import safe')"
python pgvector_search.py
```

Enter `login`. Expect chunk **3** from `sample-policy.txt`.

Run `python pgvector_search.py` again and enter `banana`. Expect **no match**.
Each search requests one query embedding. The import check makes no requests.

Keep `KNOWLEDGE_DATABASE_URL` and your existing `OPENAI_API_KEY` in `.env`.
The search reads chunks from the database and does not open `embeddings.json`.

## 3. Reuse your five-question evaluation

Copy `evaluate_semantic.py` to a new file named `evaluate_postgres.py`.
Change only its first line to:

```python
from pgvector_search import MINIMUM_SCORE, find_chunk
```

The new function returns the same three values: chunk (or `None`), score,
and query input tokens. That lets you reuse the same evaluation cases.

Run:

```bash
python evaluate_postgres.py
ruff check pgvector_search.py evaluate_postgres.py
```

This evaluation makes **five more embedding requests**. Aim for the same
**5/5** result as your JSON search. Report any failures with their scores;
do not change the threshold just to make the score pass. Tiny numerical
differences can occur between database and Python calculations.

The existing question API still uses `semantic_search.py`. The next lesson
will connect the database search to the API and handle database failures.

## Done when

Send:

```text
Import without prompt: yes/no
login result / source: __ / __
banana result: __
PostgreSQL retrieval score: __ / 5
Total evaluation query input tokens: __
Lint: pass/fail
Failed queries, if any: __
Why do we sort cosine distance from smallest to largest: __
```

Completed: reported safe import, `login` returning chunk 3 from
`sample-policy.txt`, `banana` rejected, retrieval 5/5 with 8 query input tokens,
and passing lint. Clarified distance versus similarity; correctly identified
0.1 as the first result when sorting distances 0.1 and 0.6 in ascending order.

Next: [Day 33 — connect the question API to PostgreSQL](day-33.md).

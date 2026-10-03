# Day 31 — save your embeddings in PostgreSQL

Today you will copy the three chunks from `data/embeddings.json` into your
vector database. Allow 25–30 minutes. No model calls or API credit are needed.

You will save each chunk's text, source, number, model name, and embedding.

## 1. Create the table

Create `migrations/knowledge/001_create_document_chunks.sql`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    source text NOT NULL,
    chunk_id integer NOT NULL CHECK (chunk_id > 0),
    content text NOT NULL,
    embedding_model text NOT NULL,
    embedding vector(1536) NOT NULL,
    PRIMARY KEY (source, chunk_id)
);

INSERT INTO schema_migrations (version)
VALUES ('001_create_document_chunks')
ON CONFLICT (version) DO NOTHING;
```

`vector(1536)` requires each embedding to have 1,536 values. The primary key
identifies a chunk by both its filename and its number: different files can
each have a chunk 1. See the
[pgvector storage guide](https://github.com/pgvector/pgvector#storing).

From the project root, apply the migration to the `knowledge` database:

```bash
docker compose -f compose.knowledge.yml up -d --wait vector-db
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 --single-transaction --file=- < migrations/knowledge/001_create_document_chunks.sql
```

As in Day 12, this numbered file records the schema setup. An already-exists
notice for `vector` is expected. Rerunning the migration does not add duplicate
version entries; it also does not repair an existing table with a different schema.

## 2. Add the connection setting

Add this new line to your existing `.env`:

```dotenv
KNOWLEDGE_DATABASE_URL=postgresql://knowledge_app:local_learning_only@127.0.0.1:15433/knowledge
```

Keep the existing `DATABASE_URL` setting for the classifier. The new setting
connects a Python script running on your computer to the knowledge database.
Also add `KNOWLEDGE_DATABASE_URL=` to `.env.example` to document the setting.

## 3. Write the import script

Create `import_embeddings.py` in the project root:

```python
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def main():
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    database_url = os.getenv("KNOWLEDGE_DATABASE_URL")
    if not database_url:
        raise SystemExit("Set KNOWLEDGE_DATABASE_URL in .env first.")

    saved = json.loads((root / "data" / "embeddings.json").read_text(encoding="utf-8"))
    model = saved["model"]
    chunks = saved["chunks"]
    if model != "text-embedding-3-small":
        raise SystemExit("This lesson expects text-embedding-3-small embeddings.")
    if not chunks:
        raise SystemExit("The saved file has no chunks.")

    rows = []
    for chunk in chunks:
        if len(chunk["embedding"]) != 1536:
            raise SystemExit("Each saved embedding must have 1536 values.")
        rows.append((
            chunk["source"],
            chunk["id"],
            chunk["text"],
            model,
            json.dumps(chunk["embedding"], allow_nan=False),
        ))

    with (
        psycopg.connect(database_url, connect_timeout=5) as connection,
        connection.cursor() as cursor,
    ):
        cursor.executemany(
            """
            INSERT INTO document_chunks
                (source, chunk_id, content, embedding_model, embedding)
            VALUES (%s, %s, %s, %s, %s::vector)
            ON CONFLICT (source, chunk_id) DO UPDATE SET
                content = EXCLUDED.content,
                embedding_model = EXCLUDED.embedding_model,
                embedding = EXCLUDED.embedding
            """,
            rows,
        )

    print(f"Chunks imported: {len(rows)}")
    print(f"Embedding model: {model}")


if __name__ == "__main__":
    main()
```

There are three ideas to notice:

- `%s` passes values separately from the SQL. `json.dumps` makes the vector's
  text representation, and `::vector` converts it to the database type.
  See [Psycopg parameters](https://www.psycopg.org/psycopg3/docs/basic/params.html).
- `ON CONFLICT` updates the existing source/chunk pair when you import again.
  This insert-or-update operation is called an **upsert**. See
  [PostgreSQL INSERT](https://www.postgresql.org/docs/17/sql-insert.html).
- The connection context commits when the block succeeds and rolls back if
  it raises an error. See
  [Psycopg connection contexts](https://www.psycopg.org/psycopg3/docs/basic/usage.html#with-connection).

The script uses your existing Psycopg dependency. It copies the cached vectors;
it does not import or call an embedding client.

## 4. Import, inspect, and repeat

Run:

```bash
source .venv/bin/activate
python import_embeddings.py
```

Expect `Chunks imported: 3` and `Embedding model: text-embedding-3-small`.
Check what the database stored:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT source, chunk_id, embedding_model, vector_dims(embedding) AS dimensions FROM document_chunks ORDER BY source, chunk_id;"
```

Expect three rows from `sample-policy.txt`, numbered 1, 2, and 3, each with
1,536 dimensions and the expected model name.

Now repeat the import and count the rows:

```bash
python import_embeddings.py
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT count(*) FROM document_chunks;"
ruff check import_embeddings.py
```

Expect **3 rows**, not 6, and lint passing. Finally, read a chunk's text:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT content FROM document_chunks WHERE source = 'sample-policy.txt' AND chunk_id = 3;"
```

Expect the account-access passage with password-reset guidance.

This importer adds or updates the chunks in the file. It does not remove old
database rows if a later document has fewer chunks. For this lesson, use your
existing three-chunk cache. The question API still searches the JSON file;
connecting retrieval to PostgreSQL is the next step.

## Done when

Send:

```text
Chunks imported: __
Database rows after second import: __
Dimensions per stored chunk: __
Stored embedding model: __
Chunk 3 text read back correctly: yes/no
Lint: pass/fail
Why doesn't importing twice create six rows: __
```

Completed: reported three imported chunks and three rows after a second import,
1,536 dimensions per chunk, model `text-embedding-3-small`, correct chunk 3
readback, and passing lint. Correctly identified the `(source, chunk_id)` key;
clarified that `ON CONFLICT ... DO UPDATE` updates the matching row on reruns.

Next: [Day 32 — search your vectors in PostgreSQL](day-32.md).

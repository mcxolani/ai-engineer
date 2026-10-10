# Day 36 — remove obsolete database chunks

Your proposed improvement fixes a real problem: deleted documents and paragraphs
can otherwise remain searchable. Today the importer will make `document_chunks`
match the complete, current cache. Allow 30–40 minutes.

The exercise reuses your existing four embeddings and makes **no model calls**.

## 1. Keep cleanup with the database import

The builder prepares the new cache. The importer applies it to PostgreSQL.
Putting cleanup in the importer lets these database changes share one transaction:

1. Load incoming chunks into a temporary table.
2. Insert or update the current chunks.
3. Delete database rows whose source/chunk pair is absent from that table.

If a database step fails, the transaction rolls back. Do not delete old rows
while the builder is still trying to generate their replacements.

For this small project, `documents/` owns the **whole** `document_chunks` table.
The cache must describe all its current chunks, not just one changed file.

## 2. Update the importer

Replace `import_embeddings.py` with:

```python
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from document_loader import load_chunks


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
        raise SystemExit("The saved file has no chunks; no database changes made.")

    cached_text = [
        {"id": chunk["id"], "source": chunk["source"], "text": chunk["text"]}
        for chunk in chunks
    ]
    if cached_text != load_chunks(root / "documents"):
        raise SystemExit("The cache differs from the documents. Rebuild it before importing.")

    rows = []
    for chunk in chunks:
        if len(chunk["embedding"]) != 1536:
            raise SystemExit("Each saved embedding must have 1536 values.")
        rows.append((
            chunk["source"], chunk["id"], chunk["text"], model,
            json.dumps(chunk["embedding"], allow_nan=False),
        ))

    with (
        psycopg.connect(database_url, connect_timeout=5) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "CREATE TEMP TABLE incoming_chunks "
            "(LIKE document_chunks INCLUDING ALL) ON COMMIT DROP"
        )
        cursor.executemany(
            """
            INSERT INTO incoming_chunks
                (source, chunk_id, content, embedding_model, embedding)
            VALUES (%s, %s, %s, %s, %s::vector)
            """,
            rows,
        )
        cursor.execute(
            """
            INSERT INTO document_chunks
                (source, chunk_id, content, embedding_model, embedding)
            SELECT source, chunk_id, content, embedding_model, embedding
            FROM incoming_chunks
            WHERE true
            ON CONFLICT (source, chunk_id) DO UPDATE SET
                content = EXCLUDED.content,
                embedding_model = EXCLUDED.embedding_model,
                embedding = EXCLUDED.embedding
            """
        )
        cursor.execute(
            """
            DELETE FROM document_chunks AS existing
            WHERE NOT EXISTS (
                SELECT 1 FROM incoming_chunks AS incoming
                WHERE incoming.source = existing.source
                  AND incoming.chunk_id = existing.chunk_id
            )
            """
        )
        removed = cursor.rowcount

    print(f"Chunks imported: {len(rows)}")
    print(f"Obsolete chunks removed: {removed}")
    print(f"Embedding model: {model}")


if __name__ == "__main__":
    main()
```

The text comparison checks the whole ordered list of source/chunk/text values
against the loader's current output. A stale or incomplete cache stops the
import before any database changes. An empty cache also stops: this version
does not support clearing the entire collection by importing zero chunks.

`LIKE ... INCLUDING ALL` gives the temporary table the existing table's structure
and constraints. `ON COMMIT DROP` removes the temporary table when the transaction
commits. See [PostgreSQL CREATE TABLE](https://www.postgresql.org/docs/17/sql-createtable.html).

`NOT EXISTS` finds rows without a matching incoming pair. Both parts of the key
matter: the two documents can still each keep their own chunk 1. `WHERE true`
in the insert makes the following `ON CONFLICT` unambiguous to the SQL parser.

Keep Psycopg's default transaction behavior here. Its connection context commits
on success and rolls back on error; do not add `autocommit=True` to this importer.
See [Psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

Run one importer at a time, with document files unchanged during the import.
This is a local collection sync; coordinating concurrent editing and import jobs
is a later improvement.

## 3. Add two deliberately obsolete practice rows

Keep your two text files as they are. Start the database and run the following
from the project root. The SQL copies an existing vector, so it makes no model
requests:

```bash
source .venv/bin/activate
docker compose -f compose.knowledge.yml up -d --wait vector-db
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 --single-transaction <<'SQL'
INSERT INTO document_chunks (source, chunk_id, content, embedding_model, embedding)
SELECT 'obsolete-practice.txt', 1, 'Practice row for a removed document.',
       embedding_model, embedding
FROM document_chunks
WHERE source = 'sample-policy.txt' AND chunk_id = 1
ON CONFLICT (source, chunk_id) DO NOTHING;

INSERT INTO document_chunks (source, chunk_id, content, embedding_model, embedding)
SELECT 'sample-policy.txt', 99, 'Practice row for a removed paragraph.',
       embedding_model, embedding
FROM document_chunks
WHERE source = 'sample-policy.txt' AND chunk_id = 1
ON CONFLICT (source, chunk_id) DO NOTHING;

SELECT source, chunk_id FROM document_chunks ORDER BY source, chunk_id;
SQL
```

Expect **six rows**: your four real chunks plus the two practice rows. They
represent a removed file and a removed paragraph. Do not create matching text
files, and finish the cleanup before using the assistant for questions.

## 4. Import and check cleanup

Run:

```bash
python import_embeddings.py
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT source, chunk_id FROM document_chunks ORDER BY source, chunk_id;"
```

Expect **4 imported**, **2 obsolete chunks removed**, and these remaining pairs:

```text
remote-work-policy.txt / 1
sample-policy.txt / 1
sample-policy.txt / 2
sample-policy.txt / 3
```

Then run the importer again and lint it:

```bash
python import_embeddings.py
ruff check import_embeddings.py
```

Expect **4 imported**, **0 obsolete chunks removed**, and passing lint.

In normal use, after changing or deleting a document, first rebuild the complete
cache with `python build_index.py`, then run the importer. Rebuilding uses paid
embeddings. Today you only added database practice rows, so your existing cache
already matches the files and no rebuild is needed.

## Done when

Send:

```text
Rows before cleanup: __
Chunks imported / obsolete chunks removed: __ / __
Rows after cleanup: __
Removed on second import: __
Both real chunk-1 rows preserved: yes/no
Lint: pass/fail
Why should importing current chunks and deleting obsolete chunks share one transaction: __
```

Completed: reported six rows before cleanup, four imported, two obsolete rows
removed, and four rows afterward. Repeat import removed zero rows, both real
chunk-1 pairs remained, and lint passed. Correctly explained that a failure
should roll back all changes and preserve the original database state.

Next: [Day 37 — test the importer's checks](day-37.md).

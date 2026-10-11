# Day 38 — prove rollback with PostgreSQL

Today you will make the real importer fail during cleanup and check that its
earlier updates were rolled back. Allow 25–30 minutes. No model calls are needed.

This is a manual integration exercise using a separate database named
`knowledge_rollback_practice`. Your API continues to use `knowledge`.

## 1. Prepare the practice database

From the project root:

```bash
source .venv/bin/activate
docker compose -f compose.knowledge.yml up -d --wait vector-db
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT count(*) FROM document_chunks;"
docker compose -f compose.knowledge.yml exec -T vector-db createdb -U knowledge_app knowledge_rollback_practice
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge_rollback_practice --set=ON_ERROR_STOP=1 --single-transaction --file=- < migrations/knowledge/001_create_document_chunks.sql
```

Record the main database count: expect **4**. If repeating this lesson and the
practice database already exists, skip `createdb`. If a previous attempt left
the failure trigger in place, run step 4's drop command before importing again.

Copy your current cached chunks into the practice database:

```bash
KNOWLEDGE_DATABASE_URL=postgresql://knowledge_app:local_learning_only@127.0.0.1:15433/knowledge_rollback_practice python import_embeddings.py
```

Expect **4 imported**. The connection setting before `python` applies only to
that command. Keep `.env` pointing to your main `knowledge` database.

## 2. Set up a failure after the upsert

Run this block. Every statement targets the practice database:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge_rollback_practice --set=ON_ERROR_STOP=1 --single-transaction <<'SQL'
UPDATE document_chunks
SET content = 'Old practice text'
WHERE source = 'sample-policy.txt' AND chunk_id = 1;

INSERT INTO document_chunks (source, chunk_id, content, embedding_model, embedding)
SELECT 'obsolete-practice.txt', 1, 'Obsolete practice row', embedding_model, embedding
FROM document_chunks
WHERE source = 'sample-policy.txt' AND chunk_id = 1
ON CONFLICT (source, chunk_id) DO NOTHING;

CREATE OR REPLACE FUNCTION reject_practice_cleanup() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Practice cleanup failure';
END;
$$;

CREATE OR REPLACE TRIGGER reject_practice_cleanup
BEFORE DELETE ON document_chunks
FOR EACH ROW EXECUTE FUNCTION reject_practice_cleanup();

SELECT count(*) AS rows_before_failure FROM document_chunks;
SELECT content FROM document_chunks
WHERE source = 'sample-policy.txt' AND chunk_id = 1;
SQL
```

Expect **5 rows** and `Old practice text`. The setup block commits those changes,
so they become the starting state for the import we are about to test.

The trigger makes a real SQL `DELETE` fail on purpose. This is enough to exercise
the transaction; there is no need to stop the server. See
[PostgreSQL triggers](https://www.postgresql.org/docs/17/sql-createtrigger.html).

## 3. Run the importer and inspect the result

Run the same import command:

```bash
KNOWLEDGE_DATABASE_URL=postgresql://knowledge_app:local_learning_only@127.0.0.1:15433/knowledge_rollback_practice python import_embeddings.py
```

This time, a traceback containing **`Practice cleanup failure` is expected**.
The importer first tries to replace `Old practice text` with the cached passage.
Then deletion of the obsolete row triggers the failure.

Now inspect the practice database using a new connection:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge_rollback_practice --set=ON_ERROR_STOP=1 -c "SELECT count(*) FROM document_chunks; SELECT content FROM document_chunks WHERE source = 'sample-policy.txt' AND chunk_id = 1;"
```

Expect **5 rows** and still **`Old practice text`**.

The retained old text is the key evidence: the earlier upsert was undone too.
The row count alone would only show that cleanup did not finish. Psycopg's
connection context rolls back when the error leaves the block; see
[Psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

## 4. Remove the forced failure and retry

Remove the practice trigger and its function:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge_rollback_practice --set=ON_ERROR_STOP=1 -c "DROP TRIGGER IF EXISTS reject_practice_cleanup ON document_chunks; DROP FUNCTION IF EXISTS reject_practice_cleanup();"
```

Then import again and inspect the result:

```bash
KNOWLEDGE_DATABASE_URL=postgresql://knowledge_app:local_learning_only@127.0.0.1:15433/knowledge_rollback_practice python import_embeddings.py
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge_rollback_practice --set=ON_ERROR_STOP=1 -c "SELECT count(*) FROM document_chunks; SELECT content FROM document_chunks WHERE source = 'sample-policy.txt' AND chunk_id = 1;"
```

Expect **4 imported**, **1 obsolete row removed**, **4 rows remaining**, and
the original support-hours passage in place of `Old practice text`.

Finally, check the main database count again:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT count(*) FROM document_chunks;"
```

Expect **4**, as before. The practice database can remain for later exercises.
No application code changes are needed today, and the automated suite still
contains 40 tests; this manual check does not add a pytest case.

## Done when

Send:

```text
Practice rows before failed import: __
Expected cleanup error seen: yes/no
Practice rows after failed import: __
Old practice text still present after failure: yes/no
Rows after successful retry: __
Support-hours text restored after retry: yes/no
Main database count before / after: __ / __
Why does retaining the old text prove more than retaining the row count: __
```

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

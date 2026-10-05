import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from psycopg.rows import dict_row

EMBEDDING_MODEL = "text-embedding-3-small"
MINIMUM_SCORE = 0.30

class RetrievalUnavailable(RuntimeError):
    """Document retrieval is not ready to serve questions."""


def find_chunk(query):
    query = query.strip()
    if not query:
        raise ValueError("Enter a search before requesting embeddings.")

    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    database_url = os.getenv("KNOWLEDGE_DATABASE_URL")
    if not database_url:
        raise RetrievalUnavailable("Set KNOWLEDGE_DATABASE_URL in .env first.")

    with psycopg.connect(
        database_url, connect_timeout=5, row_factory=dict_row, autocommit=True
    ) as connection:
        existing = connection.execute(
            "SELECT 1 FROM document_chunks WHERE embedding_model = %s LIMIT 1",
            (EMBEDDING_MODEL,),
        ).fetchone()
        if existing is None:
            raise RetrievalUnavailable("Import chunks for this embedding model first.")

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
        raise RetrievalUnavailable("No chunks remain for this embedding model.")

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

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

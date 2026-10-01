# Day 30 — start a vector database

Today you will start PostgreSQL with **pgvector**, an extension that stores
vectors and calculates distances between them. This is the next step toward
searching your document embeddings in a database.

Allow 15–20 minutes, plus the first Docker image download. No model calls or
API credit are needed.

## 1. Add the database configuration

Create `compose.knowledge.yml` in the project root:

```yaml
name: ai-engineer-knowledge

services:
  vector-db:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: knowledge_app
      POSTGRES_PASSWORD: local_learning_only
      POSTGRES_DB: knowledge
    ports:
      - "127.0.0.1:15433:5432"
    volumes:
      - knowledge_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U knowledge_app -d knowledge"]
      interval: 2s
      timeout: 5s
      retries: 15

volumes:
  knowledge_data:
```

This uses PostgreSQL 17 with pgvector installed. The password is for this local
learning database. Port `15433` is bound to your computer's loopback address.
The named volume holds the database files.

The top-level `name` gives this its own Compose project, as described in the
[Docker Compose documentation](https://docs.docker.com/reference/compose-file/version-and-name/).
Use `-f compose.knowledge.yml` in every command below to select this configuration.
Your existing classifier uses `compose.yml` and port `15432`.

From the project root, run:

```bash
docker compose -f compose.knowledge.yml config --quiet
docker compose -f compose.knowledge.yml up -d --wait vector-db
docker compose -f compose.knowledge.yml ps
```

Expect the database to be **healthy**. The first run downloads the image.

## 2. Enable pgvector

Run:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

Expect one row named `vector` with a version number. Installing the extension
in the image makes it available; `CREATE EXTENSION` enables it in the `knowledge`
database. Rerunning that first command is safe; an already-exists notice is expected.

## 3. Calculate similarity in SQL

Run this command exactly as written:

```bash
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 <<'SQL'
SELECT
    1 - ('[1,0,0]'::vector <=> '[1,0,0]'::vector) AS same_direction,
    1 - ('[1,0,0]'::vector <=> '[0,1,0]'::vector) AS perpendicular;
SQL
```

Expect `same_direction = 1` and `perpendicular = 0`.

`::vector` converts the written list into a vector. `<=>` calculates **cosine
distance**. Subtracting that distance from 1 gives **cosine similarity**, the
measure you used in Python. Higher similarity means closer directions; lower
distance means closer directions. See the
[pgvector guide](https://github.com/pgvector/pgvector#querying).

These are tiny, three-dimensional examples chosen for easy arithmetic. Your
saved document embeddings have 1,536 dimensions. This exercise does not generate
or import any embeddings, and similarity is still not a confidence percentage.

## 4. Check after a restart

Run:

```bash
docker compose -f compose.knowledge.yml restart vector-db
docker compose -f compose.knowledge.yml up -d --wait vector-db
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Expect `vector` again, without enabling it a second time.

Your question API currently reads `data/embeddings.json`. In the next lesson,
you will copy those existing vectors into this database without paying to
generate them again.

## Done when

Send:

```text
Vector database healthy: yes/no
Extension name / version: __ / __
Same-direction similarity: __
Perpendicular similarity: __
Extension still enabled after restart: yes/no
Why do we subtract cosine distance from 1: __
```

# Day 41 — run the knowledge API in Docker

Today, run the knowledge API and its existing database together with Compose.
Allow 25–35 minutes, plus the first image build. **No model calls are needed:**
we will check `/health` and `/sources`.

## 1. Create the API image

Create `Dockerfile.knowledge` in the project root:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN python -m pip install --no-cache-dir .

COPY knowledge_api.py ask_document.py pgvector_search.py ./

RUN useradd --create-home appuser
USER appuser

EXPOSE 8001
CMD ["uvicorn", "knowledge_api:app", "--host", "0.0.0.0", "--port", "8001"]
```

The existing package configuration includes `app`, so we copy it to install the
project dependencies. The command starts the knowledge API. Its three Python
modules are copied separately into `/app`, where Uvicorn can import them.

The API reads indexed chunks from PostgreSQL, so it does not need the documents
folder or embedding cache in its image. The existing `.dockerignore` excludes
`.env` files from the build context. Supply the API key at runtime.

## 2. Add the API service

Replace `compose.knowledge.yml` with the following. It preserves the database's
project name, settings, and named volume:

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

  knowledge-api:
    build:
      context: .
      dockerfile: Dockerfile.knowledge
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      KNOWLEDGE_DATABASE_URL: postgresql://knowledge_app:local_learning_only@vector-db:5432/knowledge
    ports:
      - "127.0.0.1:8001:8001"
    depends_on:
      vector-db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3)"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

volumes:
  knowledge_data:
```

Compose takes `OPENAI_API_KEY` from your shell or the project's `.env`. An empty
key is sufficient for today's two endpoints. Live `/ask` requests still require
a valid key and incur model usage.

There are now two database addresses:

| Caller | Database address |
| --- | --- |
| Local Python scripts | `127.0.0.1:15433` |
| Knowledge API container | `vector-db:5432` |

Inside the API container, `127.0.0.1` refers to that container. Compose lets
services reach each other using their service names and container ports.
See [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/).

Keep the local database URL in `.env` for your build/import scripts. The Compose
service supplies its own URL. `depends_on` waits for the database health check
on startup; the API health check only checks that the HTTP server responds.
See [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).

## 3. Build and check both services

Stop the local Uvicorn process with **Ctrl+C** in its terminal first, so port
8001 is available. Then run from the project root:

```bash
docker compose -f compose.knowledge.yml config --quiet
docker compose -f compose.knowledge.yml up -d --build --wait
docker compose -f compose.knowledge.yml ps
```

Expect both `vector-db` and `knowledge-api` to be healthy. This uses your existing
database volume, so the four indexed chunks should already be present. There is
no need to rebuild embeddings, import again, or recreate the schema.

If the build or startup fails, read the error and API logs:

```bash
docker compose -f compose.knowledge.yml logs --tail=50 knowledge-api
```

Open <http://127.0.0.1:8001/docs> and execute:

- `GET /health`: expect 200 and `{"status": "ok"}`.
- `GET /sources`: expect 200, remote-work count **1**, sample-policy count **3**.

The source response checks that the container can reach the database and read
its table. A healthy API alone does not prove that.

## 4. Restart the API

```bash
docker compose -f compose.knowledge.yml restart knowledge-api
docker compose -f compose.knowledge.yml up -d --wait knowledge-api
```

Execute `GET /sources` again. Expect the same two sources and counts. Restarting
the API does not remove the rows held by the separate database.

This image contains a copy of your code. After future Python changes, rebuild
and recreate the API with:

```bash
docker compose -f compose.knowledge.yml up -d --build --wait knowledge-api
```

Building and importing documents can still run from your local virtual
environment. This lesson adds no Python behavior or test cases; the suite
remains at **50 tests**.

## Done when

Send:

```text
Compose configuration valid: yes/no
Knowledge API container healthy: yes/no
Database container healthy: yes/no
GET /health status: __
GET /sources status: __
Remote-work / sample-policy chunk counts: __ / __
GET /sources after API restart: __
Why does the container use vector-db:5432 instead of localhost:15433: __
```

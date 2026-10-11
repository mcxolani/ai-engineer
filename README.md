# Support Ticket Classifier

This service classifies customer tickets for a support team.

[Project 1 walkthrough](docs/project-01.md) · [Knowledge assistant walkthrough](docs/project-02.md)


Our first project accepts a customer message and returns a category, priority,
sentiment, and summary.

## Start here

The environment is already installed in this workspace:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>. Expand `POST /tickets/classify`, click
**Try it out**, and send:

```json
{"message": "My payment went through twice"}
```

**Demo mode returns a fixed example for every message. No API key is needed.**

## Debug in VS Code

Install the Python and Python Debugger extensions, then select **Debug FastAPI**
in **Run and Debug** and press **F5**. Set a breakpoint in `app/main.py` and send
a request from <http://127.0.0.1:8000/docs>. Stop any existing server on port 8000
first. Restart the debugger after changing code.

The workspace defaults to `.venv`. If another interpreter is already selected,
use **Python: Select Interpreter** to select `.venv`. Choose **Debug pytest** to
debug the test suite, or use the Testing panel to debug individual tests.

## Understand three steps

1. `app/schemas.py` defines the input and output fields.
2. `app/main.py` receives the request.
3. `app/classifier.py` returns the demo result or calls OpenAI.

Project 1 (Days 1–15) and Days 16–41 are complete.
Next: [Day 42 — check the knowledge container in CI](docs/day-42.md) (20–30 minutes),
building toward a document knowledge assistant.
[Day 1](docs/day-01.md), [Day 2](docs/day-02.md), [Day 3](docs/day-03.md),
[Day 4](docs/day-04.md), [Day 5](docs/day-05.md), [Day 6](docs/day-06.md),
[Day 7](docs/day-07.md), [Day 8](docs/day-08.md), [Day 9](docs/day-09.md),
[Day 10](docs/day-10.md), [Day 11](docs/day-11.md), [Day 12](docs/day-12.md),
[Day 13](docs/day-13.md), [Day 14](docs/day-14.md), [Day 15](docs/day-15.md),
[Day 16](docs/day-16.md), [Day 17](docs/day-17.md), [Day 18](docs/day-18.md),
[Day 19](docs/day-19.md), [Day 20](docs/day-20.md), [Day 21](docs/day-21.md),
[Day 22](docs/day-22.md), [Day 23](docs/day-23.md), [Day 24](docs/day-24.md),
[Day 25](docs/day-25.md), [Day 26](docs/day-26.md), [Day 27](docs/day-27.md),
[Day 28](docs/day-28.md), [Day 29](docs/day-29.md), [Day 30](docs/day-30.md),
[Day 31](docs/day-31.md), [Day 32](docs/day-32.md), [Day 33](docs/day-33.md),
[Day 34](docs/day-34.md), [Day 35](docs/day-35.md), [Day 36](docs/day-36.md),
[Day 37](docs/day-37.md), [Day 38](docs/day-38.md), [Day 39](docs/day-39.md),
[Day 40](docs/day-40.md), and [Day 41](docs/day-41.md)
are available for reference.

## Later: turn on AI

Copy `.env.example` to `.env` if it doesn't exist. Set `CLASSIFIER_PROVIDER=openai` and add your
`OPENAI_API_KEY`, then restart the server. Real requests send the message to OpenAI
and incur API charges, demo does not need keys. Keep the key in `.env`, which is ignored by Git.
the `DATABASE_URL` enables the saving of the ticket to db

The implementation follows the [OpenAI Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).

## Setup on another machine

Use Python 3.12 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

## start postgress and api

```bash
docker compose config --quiet
docker compose up -d --wait db
docker compose exec -T db psql -X -U ticket_app -d tickets --set=ON_ERROR_STOP=1 --single-transaction --file=- < migrations/001_create_classifications.sql
docker compose up -d --build --wait api
docker compose ps
```

## Knowledge assistant

This project splits `.txt` files in `documents/` into paragraph chunks, embeds
them, and stores their source, chunk number, text, model name, and vector in
PostgreSQL with pgvector. `(source, chunk_id)` identifies each row.

`POST /ask` checks that stored chunks exist for the embedding model, embeds the
question, and retrieves the row with the smallest cosine distance. An optional
`source` filename restricts the candidates before choosing that row. If its
similarity meets the `0.30` minimum, the assistant generates an answer using that
passage. Otherwise, it returns no match and skips generation. Expected database
and provider failures return explicit errors. An unknown source returns no match
with a null score. Live questions incur model usage.

`GET /sources` lists the indexed filenames and their chunk counts for the current
embedding model. It reads PostgreSQL and makes no model calls.

The retrieval evaluation compares expected source/chunk pairs with the retrieved
pairs. The latest reported result is **6/6 on six development queries**; it does
not establish accuracy on all future questions.

See the [project walkthrough](docs/project-02.md), [database setup](docs/day-31.md),
and [document build/import instructions](docs/day-34.md). Set `OPENAI_API_KEY` and
`KNOWLEDGE_DATABASE_URL` in `.env` for local scripts. After setup and import,
start the API and database with:

```bash
docker compose -f compose.knowledge.yml up -d --build --wait
```

Stop any local Uvicorn process using port 8001 before starting the container.
Open <http://127.0.0.1:8001/docs> to list sources or submit a question. Compose
supplies the API container with the database address `vector-db:5432`; local
scripts continue to use `127.0.0.1:15433`. Rebuild the API image after code changes.

Checks: `pytest -q` and `ruff check .`. Tests make no paid API calls.

The [roadmap](docs/roadmap.md) lists later milestones.

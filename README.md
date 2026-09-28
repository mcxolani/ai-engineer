# Support Ticket Classifier

This service classifies customer tickets for a support team.

[Project walkthrough](docs/project-01.md)


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

Project 1 (Days 1–15) and Days 16–18 are complete.
Next: [Day 19 — create your first embedding](docs/day-19.md) (15–20 minutes),
building toward a document knowledge assistant.
[Day 1](docs/day-01.md), [Day 2](docs/day-02.md), [Day 3](docs/day-03.md),
[Day 4](docs/day-04.md), [Day 5](docs/day-05.md), [Day 6](docs/day-06.md),
[Day 7](docs/day-07.md), [Day 8](docs/day-08.md), [Day 9](docs/day-09.md),
[Day 10](docs/day-10.md), [Day 11](docs/day-11.md), [Day 12](docs/day-12.md),
[Day 13](docs/day-13.md), [Day 14](docs/day-14.md), [Day 15](docs/day-15.md),
[Day 16](docs/day-16.md), [Day 17](docs/day-17.md), and [Day 18](docs/day-18.md)
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


Checks: `pytest -q` and `ruff check .`. Tests make no paid API calls.

The [roadmap](docs/roadmap.md) lists later milestones.

# Support Ticket Classifier

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

## Understand three steps

1. `app/schemas.py` defines the input and output fields.
2. `app/main.py` receives the request.
3. `app/classifier.py` returns the demo result or calls OpenAI.

Start with the [20-minute first lesson](docs/day-01.md).

## Later: turn on AI

Copy `.env.example` to `.env`. Set `CLASSIFIER_PROVIDER=openai` and add your
`OPENAI_API_KEY`, then restart the server. Real requests send the message to OpenAI
and incur API charges. Keep the key in `.env`, which is ignored by Git.

The implementation follows the [OpenAI Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).

## Setup on another machine

Use Python 3.12 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Checks: `pytest -q` and `ruff check .`. Tests make no paid API calls.

The [roadmap](docs/roadmap.md) lists later milestones.

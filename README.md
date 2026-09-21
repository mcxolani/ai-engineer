# AI engineering lab

Start here: **Project 1 — AI Support Ticket Classifier**.

Today's outcome is a running Python API and an understanding of how a ticket
becomes validated structured data. This is a learning starter; persistence,
deployment, and quality evaluation are later milestones.

## Run it

From this directory, with Python 3.12 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> and try `POST /tickets/classify`, or run:

```bash
curl -i http://127.0.0.1:8000/tickets/classify \
  -H 'Content-Type: application/json' \
  -d '{"message":"My payment went through twice"}'
```

The default **demo provider returns the same fixed example for every valid
message**. It verifies the request flow; it does not understand the ticket.
`GET /health` and the `X-Classifier-Provider` response header identify the mode.

## Use a real model

Edit your local `.env` (ignored by Git):

```dotenv
CLASSIFIER_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Restart the server after changing `.env`. This mode sends ticket text to OpenAI
and incurs API usage charges. The model is configurable; use a Structured Outputs
compatible model available to your account. Never put credentials in source code.

The adapter uses the Responses API's Pydantic parsing helper, following the
[official Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).
The SDK has a 20-second per-attempt timeout and at most two retries, so a request
can take longer than 20 seconds overall. Missing/refused/incomplete output becomes
an error response rather than a fabricated classification.

## Read the code in this order

1. `app/schemas.py`: Python types plus runtime validation of inputs and outputs.
2. `app/main.py`: HTTP validation, dependency injection, and error handling.
3. `app/classifier.py`: the demo implementation, prompt, and async model call.
4. `app/config.py`: environment settings and credential validation.

```text
POST ticket → TicketRequest validation → classifier → Classification → JSON
```

Run `pytest -q` and `ruff check .` after activating the virtual environment.
Tests use demo/mocked providers and make no paid API calls. They verify application
behavior, not model accuracy or live account access.

Your first lesson is in [docs/day-01.md](docs/day-01.md).
The remaining milestones are in [docs/roadmap.md](docs/roadmap.md).

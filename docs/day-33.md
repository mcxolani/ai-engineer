# Day 33 — connect the question API to PostgreSQL

Today `/ask` will retrieve its passage from PostgreSQL before generating an
answer. Allow 30–40 minutes. The automated tests use no API credit; the two
manual questions normally use **two embeddings and one generation request**.

## 1. Give retrieval failures their own error type

In `pgvector_search.py`, add this after the constants, before `find_chunk`:

```python
class RetrievalUnavailable(RuntimeError):
    """Document retrieval is not ready to serve questions."""
```

In that same file, change the three `raise RuntimeError(...)` statements to
`raise RetrievalUnavailable(...)`. Keep their messages. These cover a missing
connection setting, no chunks for the model, and chunks disappearing before
the search finishes.

This gives the API a way to recognize retrieval setup failures. A result below
the threshold still returns `None` normally.

## 2. Connect the answer helper and handle failures

In `ask_document.py`, replace:

```python
from semantic_search import find_chunk
```

with:

```python
from pgvector_search import find_chunk
```

The function still returns `(chunk, score, tokens)`, so the existing answer
generation code can use it directly.

In `knowledge_api.py`, replace the imports at the top with:

```python
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ConfigDict, Field

from ask_document import answer_question
from pgvector_search import RetrievalUnavailable
```

Replace the existing `ask` route, including its decorator, with:

```python
@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    try:
        return answer_question(request.question)
    except (psycopg.Error, RetrievalUnavailable) as exc:
        raise HTTPException(503, "Document search is unavailable") from exc
    except APITimeoutError as exc:
        raise HTTPException(504, "The model provider timed out") from exc
    except RateLimitError as exc:
        raise HTTPException(503, "The model provider is temporarily unavailable") from exc
    except (APIError, RuntimeError) as exc:
        raise HTTPException(502, "The model provider could not return a usable answer") from exc
```

Catch `RetrievalUnavailable` before `RuntimeError`, because it inherits from
`RuntimeError`. The database error branch returns a fixed message rather than
connection details. Psycopg's database exceptions inherit from `psycopg.Error`.
See [Psycopg exceptions](https://www.psycopg.org/psycopg3/docs/api/errors.html).

For this exercise, database errors and missing retrieval setup return 503.
Configuration or SQL problems still need fixing; retrying alone may not help.
FastAPI converts `HTTPException` into the error response, as described in its
[error-handling guide](https://fastapi.tiangolo.com/tutorial/handling-errors/).

The old missing-JSON-file handler is gone: this route now reads the database.

## 3. Update the automated tests

In `tests/test_knowledge_api.py`, replace the imports at the top with:

```python
from unittest.mock import Mock

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from openai import APITimeoutError

import ask_document
import knowledge_api
import pgvector_search
from pgvector_search import RetrievalUnavailable
```

Replace the existing `test_errors_have_safe_messages` function **and its
parameterized decorator** with:

```python
@pytest.mark.parametrize("error,status,detail", [
    (
        RetrievalUnavailable("private setup details"),
        503,
        "Document search is unavailable",
    ),
    (
        psycopg.OperationalError("private connection details"),
        503,
        "Document search is unavailable",
    ),
    (
        APITimeoutError(request=httpx.Request("POST", "https://example.test")),
        504,
        "The model provider timed out",
    ),
    (
        RuntimeError("private provider details"),
        502,
        "The model provider could not return a usable answer",
    ),
])
def test_errors_have_safe_messages(client, answerer, error, status, detail):
    answerer.side_effect = error
    response = client.post("/ask", json={"question": "support hours"})
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    answerer.assert_called_once_with("support hours")
```

Then add this new test at the end of the file:

```python
def test_database_failure_before_models(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_DATABASE_URL", "postgresql://unused")
    monkeypatch.setattr(pgvector_search, "load_dotenv", Mock())
    connect = Mock(side_effect=psycopg.OperationalError("private connection details"))
    monkeypatch.setattr(pgvector_search.psycopg, "connect", connect)

    model_client = Mock(side_effect=AssertionError("A model must not be called"))
    monkeypatch.setattr(pgvector_search, "OpenAI", model_client)
    monkeypatch.setattr(ask_document, "OpenAI", model_client)
    monkeypatch.setattr("semantic_search.OpenAI", model_client)

    with TestClient(knowledge_api.app) as client:
        response = client.post("/ask", json={"question": "support hours"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Document search is unavailable"}
    connect.assert_called_once()
    model_client.assert_not_called()
```

This test does not use the `client` fixture that replaces `answer_question`.
It follows the real route, answer helper, and retrieval function, then simulates
a failed database connection. It also blocks model calls through the old search
module, so an incorrect import cannot spend API credit during the test.

Run from the project root:

```bash
source .venv/bin/activate
python -m pytest tests/test_knowledge_api.py -q
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check pgvector_search.py ask_document.py knowledge_api.py tests/test_knowledge_api.py
```

Expect **14 knowledge API tests**, **32 total tests**, and passing lint. These
tests require neither a running database nor an API key. They verify behavior
and error handling; they still do not measure real answer quality.

## 4. Try the connected API

Start the database, then start the API (or let your existing `--reload` server
reload the changes):

```bash
docker compose -f compose.knowledge.yml up -d --wait vector-db
uvicorn knowledge_api:app --host 127.0.0.1 --port 8001 --reload
```

Use `POST /ask` at <http://127.0.0.1:8001/docs> to send:

```json
{"question": "On which days and at what times is support available?"}
```

Expect 200, source `sample-policy.txt`, chunk 1, and `generation: completed`.
Read the answer against the support-hours passage as before.

Then send:

```json
{"question": "banana"}
```

Expect 200, null source/chunk, `generation: skipped`, and zero generation tokens.
An unsuccessful similarity match is a valid result. An unavailable database
means the search could not run, so the error test expects 503.

## Done when

Send:

```text
Knowledge API tests passed: __
Total tests passed: __
Lint: pass/fail
Hours status / source / chunk / generation: __ / __ / __ / __
Hours answer supported by the passage: yes/no
banana status / generation: __ / __
Database failure test status: __
Database failure test called a model: yes/no
Why is an unavailable database different from no matching passage: __
```

Completed: reported 14 knowledge API tests, 32 total tests, and passing lint.
Hours returned 200 with supported content, source `sample-policy.txt`, chunk 1,
and completed generation; `banana` returned 200 with skipped generation.
The initially reported database-failure status of 502 was corrected by inspecting
the code and rerunning the dedicated test: it passes with 503 and no model calls.
Correctly explained that unavailable search must be distinguished from no match.

Next: [Day 34 — answer questions from two documents](day-34.md).

# Day 29 — test the question API

Today you will turn yesterday's manual checks into automated tests.
Allow about 25–30 minutes. These tests make no paid model calls.

The idea: give the API a fake `answer_question` function, send a request,
and check its response. You control what the fake returns or raises.

## 1. Create the test file

Create `tests/test_knowledge_api.py` and add:

```python
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APITimeoutError

import knowledge_api


@pytest.fixture
def answerer(monkeypatch):
    fake = Mock(return_value={
        "answer": "Support is available Monday to Friday, 09:00 to 17:00.",
        "source": "sample-policy.txt",
        "chunk_id": 1,
        "retrieval_score": 0.57,
        "generation": "completed",
        "embedding_input_tokens": 3,
        "generation_input_tokens": 100,
        "generation_output_tokens": 20,
    })
    monkeypatch.setattr(knowledge_api, "answer_question", fake)
    return fake


@pytest.fixture
def client(answerer):
    with TestClient(knowledge_api.app, raise_server_exceptions=False) as client:
        yield client


def test_health(client, answerer):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    answerer.assert_not_called()


def test_answer_and_metadata(client, answerer):
    response = client.post("/ask", json={"question": "  support hours  "})
    assert response.status_code == 200
    assert response.json() == answerer.return_value
    answerer.assert_called_once_with("support hours")


def test_no_match_is_success(client, answerer):
    answerer.return_value = {
        "answer": "I couldn't find a suitable passage in the document.",
        "source": None,
        "chunk_id": None,
        "retrieval_score": 0.06,
        "generation": "skipped",
        "embedding_input_tokens": 1,
        "generation_input_tokens": 0,
        "generation_output_tokens": 0,
    }
    response = client.post("/ask", json={"question": "banana"})
    assert response.status_code == 200
    assert response.json() == answerer.return_value
    answerer.assert_called_once_with("banana")


@pytest.mark.parametrize("body", [
    {},
    {"question": "   "},
    {"question": "x" * 2001},
    {"question": 42},
    {"question": "support hours", "admin": True},
])
def test_invalid_input_skips_answerer(client, answerer, body):
    response = client.post("/ask", json=body)
    assert response.status_code == 422
    answerer.assert_not_called()


@pytest.mark.parametrize("error,status,detail", [
    (
        FileNotFoundError("private backend details"),
        503,
        "Build the document index before asking questions",
    ),
    (
        APITimeoutError(request=httpx.Request("POST", "https://example.test")),
        504,
        "The model provider timed out",
    ),
    (
        RuntimeError("private backend details"),
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


def test_invalid_helper_response_is_rejected(client, answerer):
    answerer.return_value["generation"] = "unknown"
    response = client.post("/ask", json={"question": "support hours"})
    assert response.status_code == 500
    answerer.assert_called_once_with("support hours")
```

## 2. Understand the setup

`TestClient` sends requests directly to your application inside the test process.
You do not need to start Uvicorn. See the
[FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/).

The `answerer` fixture creates a fresh fake for each test. `return_value` sets
its answer; `side_effect` makes it raise an error. `monkeypatch` temporarily
replaces the function and restores it after the test. See the
[pytest monkeypatch guide](https://docs.pytest.org/en/stable/how-to/monkeypatch.html).

Patch `knowledge_api.answer_question`: that is the name the route uses.
The `client` fixture depends on `answerer`, so the replacement happens before
any test request. No saved index or API key is needed for these new tests.
The token counts and similarity scores above are invented test data.

`raise_server_exceptions=False` lets the last test inspect HTTP 500 when the
helper returns an invalid response. Invalid client input produces 422;
invalid server output is a server error.

These tests check routing, validation, metadata, and error handling. They do
not measure retrieval or answer quality, because the real helper never runs.
Your [Day 26 answer checks](day-26.md) still serve that purpose.

## 3. Run the tests

From the project root:

```bash
source .venv/bin/activate
python -m pytest tests/test_knowledge_api.py -q
```

Expect **12 passed**. The parameterized tests run once per listed case.

Then check both projects together and lint your new file:

```bash
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check tests/test_knowledge_api.py
```

Expect **30 passed**: the existing 18 tests plus 12 new ones. The environment
values above keep the full suite in demo mode with no real database connection.
Expect lint to pass too.

## Done when

Send:

```text
Knowledge API tests passed: __
Total tests passed: __
Lint: pass/fail
Invalid input called the answer helper: yes/no
No-match status: __
Timeout status: __
Why can these tests pass while a real answer is wrong: __
```

Completed: reported 12 knowledge API tests and 30 total tests passing, with lint
passing. No-match returned 200 and timeout returned 504. Corrected the initial
invalid-input answer: the helper is not called, as checked by
`assert_not_called()`. After clarification, correctly explained that the tests
use predefined responses and do not call the real retrieval/generation helper.

Next: [Day 30 — start a vector database](day-30.md).

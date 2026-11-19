# Day 47 — expose the ticket assistant through the API

Today, add one endpoint to the existing support API for the complete ticket-tool
flow. Allow 30–40 minutes. Automated tests make no model calls. One live request
makes **two paid model requests and one database read**.

## 1. Pass the database URL into the assistant

In `ticket_assistant.py`, change the function definition and executor call:

```python
def answer_ticket(question, database_url):
    first = request_lookup(question)
    tool_output = asyncio.run(execute_lookup(first, database_url))
```

In its `if __name__ == "__main__"` block, replace the call with:

```python
    result = answer_ticket(
        "What category and priority are saved for ticket 4?",
        os.getenv("DATABASE_URL", ""),
    )
```

The route will supply its configured database URL explicitly. Keep the existing
`os` import: the command-line demonstration still reads the URL after
`request_lookup` loads `.env`.

In `tests/test_ticket_assistant.py`, update every `answer_ticket(...)` call to
pass `"test-db"` as its second argument. In `test_answer_receives_question_call_and_result`,
update this assertion:

```python
    flow.execute.assert_awaited_once_with(flow.first, "test-db")
```

## 2. Add request and response models

At the end of `app/schemas.py`, add:

```python
class TicketAssistantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=2000)


class TicketAssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    ticket_id: int = Field(gt=0)
    tool_status: Literal["found", "not_found"]
    call_id: str = Field(min_length=1)
    generation: Literal["completed"]
```

The API returns the ticket ID and tool status so callers can distinguish a
retrieved record from a missing one. It does not return the whole stored ticket.

## 3. Add the route and error mapping

In `app/main.py`, add these imports after the existing `app.schemas` import:

```python
from support_tools import ToolUnavailable
from ticket_assistant import answer_ticket
```

Extend the existing `from app.schemas import ...` import to include
`TicketAssistantRequest` and `TicketAssistantResponse`.

Add this endpoint below `classify_ticket`:

```python
@app.post("/assistant/tickets/ask", response_model=TicketAssistantResponse)
def ask_about_ticket(request: TicketAssistantRequest):
    database_url = settings.database_url.get_secret_value()
    if not database_url:
        raise HTTPException(503, "Database is not configured")

    try:
        result = answer_ticket(request.question, database_url)
    except ToolUnavailable as exc:
        raise HTTPException(503, "Ticket lookup is unavailable") from exc
    except APITimeoutError as exc:
        raise HTTPException(504, "The model provider timed out") from exc
    except RateLimitError as exc:
        raise HTTPException(503, "The model provider is temporarily unavailable") from exc
    except (APIError, RuntimeError, ValueError) as exc:
        raise HTTPException(502, "The assistant could not return a usable answer") from exc

    tool_result = result["tool_result"]
    if tool_result["status"] == "found":
        ticket_id = tool_result["ticket"]["id"]
    else:
        ticket_id = tool_result["ticket_id"]

    return {
        "answer": result["answer"],
        "ticket_id": ticket_id,
        "tool_status": tool_result["status"],
        "call_id": result["call_id"],
        "generation": result["generation"],
    }
```

The route maps errors without exposing database or model details. A valid missing
ticket remains a normal 200 response with `tool_status: "not_found"`; an
unavailable database remains 503. The model never chooses the database URL—it
comes from server configuration, not the HTTP body or tool arguments.

## 4. Test the HTTP boundary

In `tests/test_api.py`, add these imports:

```python
from support_tools import ToolUnavailable
from pydantic import SecretStr
```

`SecretStr` is already imported inside the existing saving test. Move it to the
top-level imports, after `from openai ...`, then remove the local
`from pydantic import SecretStr` line from the old test. Keep `ToolUnavailable`
with the other project imports.

Append these tests:

```python
@pytest.fixture
def assistant(client, monkeypatch):
    main.settings.database_url = SecretStr("postgresql://unused-in-test")
    fake = Mock(return_value={
        "answer": "Ticket 4 is technical with medium priority.",
        "call_id": "call_test_4",
        "tool_result": {"status": "found", "ticket": {"id": 4}},
        "generation": "completed",
    })
    monkeypatch.setattr(main, "answer_ticket", fake)
    return fake


def test_assistant_answer_and_metadata(client, assistant):
    response = client.post(
        "/assistant/tickets/ask",
        json={"question": "  What is saved for ticket 4?  "},
    )
    assert response.status_code == 200
    assert response.json() == {
        "answer": "Ticket 4 is technical with medium priority.",
        "ticket_id": 4,
        "tool_status": "found",
        "call_id": "call_test_4",
        "generation": "completed",
    }
    assistant.assert_called_once_with("What is saved for ticket 4?", "postgresql://unused-in-test")


def test_assistant_not_found_is_success(client, assistant):
    assistant.return_value["tool_result"] = {"status": "not_found", "ticket_id": 999}
    assistant.return_value["answer"] = "Ticket 999 was not found."
    response = client.post("/assistant/tickets/ask", json={"question": "ticket 999"})
    assert response.status_code == 200
    assert response.json()["ticket_id"] == 999
    assert response.json()["tool_status"] == "not_found"


@pytest.mark.parametrize("body", [
    {}, {"question": "   "}, {"question": "x" * 2001}, {"question": 4},
    {"question": "ticket 4", "database_url": "postgresql://attacker"},
])
def test_invalid_assistant_input_skips_helper(client, assistant, body):
    response = client.post("/assistant/tickets/ask", json=body)
    assert response.status_code == 422
    assistant.assert_not_called()


def test_assistant_needs_configured_database(client, monkeypatch):
    main.settings.database_url = SecretStr("")
    helper = Mock()
    monkeypatch.setattr(main, "answer_ticket", helper)
    response = client.post("/assistant/tickets/ask", json={"question": "ticket 4"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not configured"}
    helper.assert_not_called()


@pytest.mark.parametrize("error,status,detail", [
    (ToolUnavailable("private database details"), 503, "Ticket lookup is unavailable"),
    (APITimeoutError(request=httpx.Request("POST", "https://example.test")), 504, "The model provider timed out"),
    (RuntimeError("private model details"), 502, "The assistant could not return a usable answer"),
])
def test_assistant_errors_are_safe(client, assistant, error, status, detail):
    assistant.side_effect = error
    response = client.post("/assistant/tickets/ask", json={"question": "ticket 4"})
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert "private" not in response.text
```

Run:

```bash
source .venv/bin/activate
python -m pytest tests/test_api.py tests/test_ticket_assistant.py -q
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check app/main.py app/schemas.py ticket_assistant.py tests/test_api.py tests/test_ticket_assistant.py
```

Expect **29 Project 1 API tests**, **85 total tests**, and passing lint. These
new tests use a fake assistant helper; they do not call a real model or database.

## 5. Use the endpoint once

Start a temporary local server on port 8002. It can run beside a Docker API on
port 8000:

```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8002
```

In another terminal, use `/docs` at <http://127.0.0.1:8002/docs> to submit:

```json
{"question": "What category and priority are saved for ticket 4?"}
```

Expect 200, ticket ID 4, `tool_status: "found"`, `generation: "completed"`,
and an answer supported by stored category and priority. This runs the Day 46
flow: two paid model requests and one database read. Stop Uvicorn with Ctrl+C
after the test. The endpoint only reads a ticket; it does not alter the record.

## Done when

Send:

```text
Project API tests passed: __
Total tests passed: __
Lint: pass/fail
POST assistant status: __
Ticket ID / tool status / generation: __ / __ / __
Answer agrees with stored category and priority: yes/no
Invalid-input test called the assistant helper: yes/no
Missing-database status: __
Tool-unavailable status: __
Why is database_url rejected in the request body: __
```

Completed: reported 29 Project API tests, 85 total tests, successful endpoint
response for ticket 4, and 503 for missing database and unavailable lookup.
The answer agreed with the stored technical / medium classification. Correctly
explained that `extra="forbid"` rejects a client-provided database URL. The
report said invalid input called the assistant helper, but the test asserts the
opposite: invalid input returns 422 before the helper is called. Targeted lint
and all 35 relevant API/assistant tests passed on recheck.

Next: [Day 48 — package the ticket assistant in Docker](day-48.md).

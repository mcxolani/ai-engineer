# Day 45 — execute the requested lookup

Today, your application will run the lookup requested by the model and prepare
its result for a later reply. Allow 30–40 minutes. The automated tests make no
model calls; the manual demonstration makes **one paid model request** and one
database read.

## 1. Add the executor

Create `execute_ticket_tool.py`:

```python
import asyncio
import json
import os

from request_ticket_tool import request_lookup
from support_tools import lookup_ticket


async def execute_lookup(response, database_url):
    if response.status != "completed":
        raise ValueError("The model response did not complete.")

    calls = [item for item in response.output if item.type == "function_call"]
    if len(calls) != 1:
        raise ValueError("Expected exactly one function call.")

    call = calls[0]
    if call.name != "lookup_ticket":
        raise ValueError("Unsupported function name.")

    arguments = json.loads(call.arguments)
    result = await lookup_ticket(arguments, database_url)
    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": json.dumps(result),
    }


def main():
    response = request_lookup("Look up saved ticket 4.")
    output = asyncio.run(execute_lookup(response, os.getenv("DATABASE_URL", "")))
    print(f"Output type: {output['type']}")
    print(f"Call ID: {output['call_id']}")
    print(json.dumps(json.loads(output["output"]), indent=2))
    print("Result sent to model: no")


if __name__ == "__main__":
    main()
```

`request_lookup` loads `.env` and obtains a model response, as in Day 44.
`execute_lookup` then accepts exactly one call to the known function. The
application chooses which Python function runs through the explicit name check.

`json.loads` parses the arguments. The existing `lookup_ticket` function still
validates the ticket ID before reading PostgreSQL. Its unavailable-storage
exception propagates to the caller; it is not converted into `not_found`.

The returned dictionary has the function-result format: `call_id` connects it
to the request, and `output` contains the serialized result. We only prepare
and print it today. See [OpenAI function results](https://developers.openai.com/api/docs/guides/function-calling).

## 2. Test routing and result handling

Create `tests/test_execute_ticket_tool.py`:

```python
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import execute_ticket_tool
from support_tools import ToolUnavailable


@pytest.fixture
def response():
    call = SimpleNamespace(
        type="function_call",
        name="lookup_ticket",
        arguments='{"ticket_id": 4}',
        call_id="call_test_4",
    )
    return SimpleNamespace(status="completed", output=[call])


@pytest.fixture
def lookup(monkeypatch):
    fake = AsyncMock()
    monkeypatch.setattr(execute_ticket_tool, "lookup_ticket", fake)
    return fake


@pytest.mark.parametrize("result", [
    {"status": "found", "ticket": {"id": 4}},
    {"status": "not_found", "ticket_id": 4},
])
def test_result_keeps_call_id(response, lookup, result):
    lookup.return_value = result
    output = asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))

    assert output["type"] == "function_call_output"
    assert output["call_id"] == "call_test_4"
    assert json.loads(output["output"]) == result
    lookup.assert_awaited_once_with({"ticket_id": 4}, "test-db")


@pytest.mark.parametrize("problem", ["incomplete", "missing", "multiple", "unknown"])
def test_invalid_response_skips_lookup(response, lookup, problem):
    if problem == "incomplete":
        response.status = "incomplete"
    elif problem == "missing":
        response.output = []
    elif problem == "multiple":
        response.output = response.output * 2
    else:
        response.output[0].name = "delete_ticket"

    with pytest.raises(ValueError):
        asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))
    lookup.assert_not_called()


def test_invalid_json_skips_lookup(response, lookup):
    response.output[0].arguments = "not JSON"
    with pytest.raises(json.JSONDecodeError):
        asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))
    lookup.assert_not_called()


def test_storage_failure_propagates(response, lookup):
    lookup.side_effect = ToolUnavailable("Ticket storage is unavailable")
    with pytest.raises(ToolUnavailable, match="Ticket storage is unavailable"):
        asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))
    lookup.assert_awaited_once_with({"ticket_id": 4}, "test-db")
```

These cases use a fake model response and a fake lookup function. Your Day 43
tests continue to check ID validation and the database boundary inside the real
lookup function.

Run:

```bash
source .venv/bin/activate
python -m pytest tests/test_execute_ticket_tool.py -q
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check execute_ticket_tool.py tests/test_execute_ticket_tool.py
```

Expect **8 executor tests**, **68 total tests**, and passing lint.

## 3. Run the real lookup

Use your existing `.env` values for `OPENAI_API_KEY` and Project 1's
`DATABASE_URL`. Start the ticket database, then run the new script once:

```bash
docker compose up -d --wait db
python execute_ticket_tool.py
```

Expect output type `function_call_output`, a call ID, and a result containing
`status: found`, ticket ID 4, and category `technical`. It is the stored result
you read in Day 43. If using another saved ticket, update the question in `main`.

This time the database has been queried: `await lookup_ticket(...)` executed
the application function. The final line still says `Result sent to model: no`
because there is no second model request yet. The ticket content stays in your
application during this demonstration.

## Done when

Send:

```text
Executor tests passed: __
Total tests passed: __
Lint: pass/fail
Output type: __
Call ID present: yes/no
Ticket ID / status / category: __ / __ / __
Unknown-function test called lookup: yes/no
Invalid-JSON test called lookup: yes/no
Result sent to model: yes/no
Why must the result keep the original call_id: __
```

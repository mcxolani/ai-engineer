# Day 43 — build a read-only ticket tool

Today starts Project 3: support tools. Reuse Project 1's saved tickets to build
a lookup function. Allow 30–40 minutes. **No model calls are needed.**

With function calling, a model can request a function and supply arguments;
your application executes the function and returns its result. Today we build
and test that application function, then call it directly from Python.
See [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).

## 1. Create the tool function

Create `support_tools.py` in the project root:

```python
import psycopg
from pydantic import BaseModel, ConfigDict, Field

from app.database import get_classification


class TicketLookupArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ticket_id: int = Field(gt=0, le=9223372036854775807)


class ToolUnavailable(RuntimeError):
    """The tool could not access its data source."""


async def lookup_ticket(arguments: dict, database_url: str) -> dict:
    args = TicketLookupArguments.model_validate(arguments)
    if not database_url:
        raise ToolUnavailable("Ticket storage is not configured")

    try:
        saved = await get_classification(database_url, args.ticket_id)
    except psycopg.Error as exc:
        raise ToolUnavailable("Ticket storage is unavailable") from exc

    if saved is None:
        return {"status": "not_found", "ticket_id": args.ticket_id}

    return {"status": "found", "ticket": saved.model_dump(mode="json")}
```

The function reuses the existing parameterized database query. Its only tool
argument is `ticket_id`; the application supplies `database_url` separately.
The ID must fit the database's positive `bigint` range.

`strict=True` rejects strings such as `"4"` and booleans such as `True` instead
of treating them as integer IDs. `extra="forbid"` rejects unexpected fields.
See [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/).

Validation happens before database access. A valid but absent ID returns
`not_found`; a database failure raises `ToolUnavailable`. Those are different
outcomes, just as no matching passage differs from a failed search service.

`model_dump(mode="json")` converts the stored timestamp into a JSON-compatible
value. This lets a future caller serialize the result without special handling.
The function reads a stored classification; it does not classify the ticket again.

## 2. Test the boundary

Create `tests/test_support_tools.py`:

```python
import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import psycopg
import pytest
from pydantic import ValidationError

import support_tools
from app.schemas import Classification, SavedClassification

DATABASE_URL = "postgresql://unused-in-test"


@pytest.fixture
def reader(monkeypatch):
    fake = AsyncMock(return_value=None)
    monkeypatch.setattr(support_tools, "get_classification", fake)
    return fake


def test_ticket_found(reader):
    reader.return_value = SavedClassification(
        id=4,
        message="Photo upload fails.",
        result=Classification(
            category="technical",
            priority="medium",
            sentiment="neutral",
            summary="Photo upload fails.",
        ),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = asyncio.run(support_tools.lookup_ticket({"ticket_id": 4}, DATABASE_URL))

    assert result["status"] == "found"
    assert result["ticket"]["id"] == 4
    assert result["ticket"]["result"]["category"] == "technical"
    assert json.loads(json.dumps(result)) == result
    reader.assert_awaited_once_with(DATABASE_URL, 4)


def test_ticket_not_found(reader):
    result = asyncio.run(support_tools.lookup_ticket({"ticket_id": 999}, DATABASE_URL))
    assert result == {"status": "not_found", "ticket_id": 999}
    reader.assert_awaited_once_with(DATABASE_URL, 999)


@pytest.mark.parametrize("arguments", [
    {},
    {"ticket_id": 0},
    {"ticket_id": "4"},
    {"ticket_id": True},
    {"ticket_id": 9223372036854775808},
    {"ticket_id": 4, "admin": True},
])
def test_invalid_arguments_skip_database(reader, arguments):
    with pytest.raises(ValidationError):
        asyncio.run(support_tools.lookup_ticket(arguments, DATABASE_URL))
    reader.assert_not_called()


def test_missing_configuration_skips_database(reader):
    with pytest.raises(support_tools.ToolUnavailable, match="not configured"):
        asyncio.run(support_tools.lookup_ticket({"ticket_id": 4}, ""))
    reader.assert_not_called()


def test_database_failure_is_not_not_found(reader):
    reader.side_effect = psycopg.OperationalError("private connection details")
    with pytest.raises(support_tools.ToolUnavailable) as error:
        asyncio.run(support_tools.lookup_ticket({"ticket_id": 4}, DATABASE_URL))
    assert str(error.value) == "Ticket storage is unavailable"
    reader.assert_awaited_once_with(DATABASE_URL, 4)
```

Run:

```bash
source .venv/bin/activate
python -m pytest tests/test_support_tools.py -q
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check support_tools.py tests/test_support_tools.py
```

Expect **10 tool tests**, **60 total tests**, and passing lint. These tests replace
the database reader with a fake; they do not connect to PostgreSQL.

## 3. Read one real saved ticket

Start the Project 1 database:

```bash
docker compose up -d --wait db
```

Your local `.env` should have Project 1's database URL:

```dotenv
DATABASE_URL=postgresql://ticket_app:local_learning_only@127.0.0.1:15432/tickets
```

This is separate from `KNOWLEDGE_DATABASE_URL`. The ticket API does not need to
be running because the tool calls the existing database helper directly.

From the project root, run:

```bash
python - <<'PY'
import asyncio
import json
import os

from dotenv import load_dotenv

from support_tools import lookup_ticket

load_dotenv(".env")
result = asyncio.run(
    lookup_ticket({"ticket_id": 4}, os.getenv("DATABASE_URL", ""))
)
print(json.dumps(result, indent=2))
PY
```

Use ticket 4 from your earlier save/read demo, or another ID you know exists.
For the original ticket 4, expect `status: found` and category `technical`.
If it returns `not_found`, confirm which saved ID is present in your database;
do not change the tool to invent a ticket.

This is a direct Python call. We have not connected the function to a model yet.
Argument validation checks the input shape; it does not establish who may read
a ticket. The exercise uses your local learning data.

## Done when

Send:

```text
Tool tests passed: __
Total tests passed: __
Lint: pass/fail
Real ticket ID / status / category: __ / __ / __
Invalid arguments called the database reader: yes/no
Missing-ticket test status: __
Database-failure exception: __
Who executes a requested function tool: the model or your application: __
```

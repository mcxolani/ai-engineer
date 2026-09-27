# Day 10: let the API save

Allow 30–40 minutes. Today the API will classify a message, save its result, and
return the saved ID in a response header. The JSON body keeps its four fields.

## 1. Read the database setting

Inside `Settings` in `app/config.py`, add this field alongside `openai_model`:

```python
    database_url: SecretStr = SecretStr("")
```

`SecretStr` is already imported. Your `.env` already has `DATABASE_URL` from Day 9.
For this learning app, an empty URL disables saving; a configured URL enables it.

## 2. Add the saving function

Create `app/database.py`:

```python
import psycopg
from psycopg.types.json import Jsonb

from app.schemas import Classification


async def save_classification(
    database_url: str, message: str, result: Classification
) -> int:
    async with await psycopg.AsyncConnection.connect(
        database_url, connect_timeout=5
    ) as connection:
        cursor = await connection.execute(
            "INSERT INTO classifications (message, result) VALUES (%s, %s) RETURNING id",
            (message, Jsonb(result.model_dump())),
        )
        row = await cursor.fetchone()
        saved_id = row[0]

    return saved_id
```

The return happens after the connection block exits successfully and commits.
We use Psycopg's async connection so database waiting can yield to other requests.
See the [official async connection guide](https://www.psycopg.org/psycopg3/docs/advanced/async.html).

## 3. Call it from the route

In `app/main.py`, add these imports:

```python
import psycopg
from app.database import save_classification
```

Inside `classify_ticket`, replace only this line:

```python
        return await classify_message(ticket.message, settings)
```

with:

```python
        result = await classify_message(ticket.message, settings)
        database_url = settings.database_url.get_secret_value()
        if database_url:
            saved_id = await save_classification(database_url, ticket.message, result)
            response.headers["X-Classification-ID"] = str(saved_id)
        return result
```

Keep the existing `except` blocks. Add one more at the same indentation:

```python
    except psycopg.Error as exc:
        raise HTTPException(503, "Could not save the classification") from exc
```

The API reports a database failure instead of claiming the result was saved.
The model call happens first, so a failed save can still incur model usage. Also,
requests are not deduplicated: sending a request twice can create two rows.

## 4. Check locally, then try one request

In `tests/test_api.py`, update the existing fixture's `Settings(...)` call to
explicitly disable database saving:

```python
Settings(_env_file=None, classifier_provider="demo", database_url="")
```

This keeps the existing tests independent of your local database. Add these tests
at the end of the same test file to check saving and its error response:

```python
@pytest.mark.parametrize("fails", [False, True])
def test_api_saving(client, monkeypatch, fails):
    import psycopg
    from pydantic import SecretStr

    main.settings.database_url = SecretStr("postgresql://unused-in-test")
    save = AsyncMock(return_value=42)
    if fails:
        save.side_effect = psycopg.OperationalError("private database details")
    monkeypatch.setattr(main, "save_classification", save)

    response = client.post("/tickets/classify", json={"message": "Duplicate payment"})
    save.assert_awaited_once()
    assert save.call_args.args[1] == "Duplicate payment"
    if fails:
        assert response.status_code == 503
        assert response.json() == {"detail": "Could not save the classification"}
        assert "X-Classification-ID" not in response.headers
    else:
        assert response.status_code == 200
        assert response.headers["X-Classification-ID"] == "42"
        assert response.json() == save.call_args.args[2].model_dump()
```

Run `pytest -q` from your activated virtual environment. These tests mock saving;
they do not make database writes or paid API calls.

Start the database with `docker compose up -d --wait db`, then restart the API.
Check your `.env` still sets `CLASSIFIER_PROVIDER=openai` and `DATABASE_URL`.
Send one duplicate-payment ticket through <http://127.0.0.1:8000/docs>. Find
`x-classification-id` in the **response headers** and note its value.

Read that row back, replacing `4` with the returned ID:

```bash
docker compose exec db psql -U ticket_app -d tickets -c "SELECT id, message, result->>'category' AS category FROM classifications WHERE id = 4;"
```

**Retire `save_ticket.py` after this change.** It inserts its own row after calling
the API and would now create a duplicate. Use `/docs` or an HTTP-only client.
Running `evaluate.py` now saves six rows when `DATABASE_URL` is configured.

You're done when a single API request saves a row and its header identifies the
same row in PostgreSQL. Send:

```text
Tests passed: __
HTTP status: __
X-Classification-ID: __
Category read back: __
```

Next session: retrieve a saved classification through the API.

Completed: 15 tests passed, HTTP 200, `X-Classification-ID: 4`. Row 4 contains
the photo-upload error message and category `technical`, verified in PostgreSQL.

Next: [Day 11 — read a saved ticket](day-11.md).

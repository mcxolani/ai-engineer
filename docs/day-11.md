# Day 11: read a saved ticket

Allow 25–35 minutes. Add `GET /tickets/{classification_id}` so a client can read
a stored result. This endpoint makes no model calls and creates no new rows.

## 1. Describe the saved response

In `app/schemas.py`, add `from datetime import datetime` to the imports. Then add
this model below `Classification`:

```python
class SavedClassification(BaseModel):
    id: int
    message: str
    result: Classification
    created_at: datetime
```

It includes both the original message and its classification. The timestamp
comes from PostgreSQL and is returned as a date-time string in JSON.

## 2. Read one row

In `app/database.py`, add these imports alongside the existing ones:

```python
from psycopg.rows import dict_row
from app.schemas import SavedClassification
```

Keep `save_classification` and add this function below it:

```python
async def get_classification(
    database_url: str, classification_id: int
) -> SavedClassification | None:
    async with await psycopg.AsyncConnection.connect(
        database_url, connect_timeout=5, row_factory=dict_row
    ) as connection:
        cursor = await connection.execute(
            "SELECT id, message, result, created_at FROM classifications WHERE id = %s",
            (classification_id,),
        )
        row = await cursor.fetchone()

    if row is None:
        return None
    return SavedClassification.model_validate(row)
```

`dict_row` makes column names into dictionary keys, matching the response model.
The comma in `(classification_id,)` makes a one-item tuple for the SQL parameters.
See [Psycopg row factories](https://www.psycopg.org/psycopg3/docs/advanced/rows.html).

## 3. Add the GET route

In `app/main.py`, add these imports, keeping the existing imports too:

```python
from fastapi import Path
from app.database import get_classification
from app.schemas import SavedClassification
```

Add the route at the bottom of the file:

```python
@app.get("/tickets/{classification_id}", response_model=SavedClassification)
async def read_ticket(
    classification_id: int = Path(gt=0, le=9223372036854775807),
) -> SavedClassification:
    database_url = settings.database_url.get_secret_value()
    if not database_url:
        raise HTTPException(503, "Database is not configured")
    try:
        saved = await get_classification(database_url, classification_id)
    except psycopg.Error as exc:
        raise HTTPException(503, "Could not read the classification") from exc

    if saved is None:
        raise HTTPException(404, "Classification not found")
    return saved
```

`Path` restricts IDs to positive values that fit PostgreSQL's `bigint`. Invalid IDs
receive 422 before the query runs. A valid but missing ID receives 404. A database
error receives 503. See [FastAPI path validation](https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/).

## 4. Check the behavior

Add this test to `tests/test_api.py`. It covers a found row, a missing row, and a
database failure, and checks that reading never calls the classifier:

```python
@pytest.mark.parametrize("status", [200, 404, 503])
def test_read_saved_ticket(client, monkeypatch, status):
    import psycopg
    from pydantic import SecretStr
    from app.schemas import SavedClassification

    saved = SavedClassification(
        id=4,
        message="The photo uploader shows an error.",
        result=Classification(
            category="technical", priority="medium", sentiment="neutral",
            summary="Photo upload fails.",
        ),
        created_at="2026-09-27T12:00:00Z",
    )
    main.settings.database_url = SecretStr("postgresql://unused-in-test")
    read = AsyncMock(return_value=saved if status == 200 else None)
    if status == 503:
        read.side_effect = psycopg.OperationalError("private database details")
    model = AsyncMock()
    monkeypatch.setattr(main, "get_classification", read)
    monkeypatch.setattr(main, "classify_message", model)

    response = client.get("/tickets/4")
    assert response.status_code == status
    read.assert_awaited_once_with("postgresql://unused-in-test", 4)
    model.assert_not_called()
    if status == 200:
        assert response.json() == saved.model_dump(mode="json")
    else:
        expected = "Classification not found" if status == 404 else "Could not read the classification"
        assert response.json() == {"detail": expected}
```

Run `pytest -q` in your activated environment. With the existing tests, expect
18 to pass. These tests use mocked database reads.

Start PostgreSQL if needed, then restart the API. Open these URLs:

- <http://127.0.0.1:8000/tickets/4>: your saved photo-upload ticket, category `technical`.
- <http://127.0.0.1:8000/tickets/999999>: 404, assuming you haven't created that ID.
- <http://127.0.0.1:8000/tickets/0>: 422 because the ID is invalid.

You can also use `/docs` to see the HTTP status codes. Repeating GET should read
the same saved content without new token-usage output in the server terminal.

Send:

```text
Tests passed: __
GET /tickets/4 status: __
Category returned: __
Missing ID status: __
Invalid ID status: __
```

Next session: make database setup repeatable with a schema migration.

# Day 40 — list available sources

Callers can now filter by filename, but they need to know which filenames exist.
Today, add `GET /sources` to list the documents stored for the current embedding
model. Allow 25–35 minutes. **No model calls or new embeddings are needed.**

## 1. Read the source names and counts

In `pgvector_search.py`, add this function above the `if __name__` block.
The imports and `EMBEDDING_MODEL` constant already exist:

```python
def list_sources():
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    database_url = os.getenv("KNOWLEDGE_DATABASE_URL")
    if not database_url:
        raise RetrievalUnavailable("Set KNOWLEDGE_DATABASE_URL in .env first.")

    with psycopg.connect(
        database_url, connect_timeout=5, row_factory=dict_row, autocommit=True
    ) as connection:
        rows = connection.execute(
            """
            SELECT source, count(*) AS chunk_count
            FROM document_chunks
            WHERE embedding_model = %s
            GROUP BY source
            ORDER BY source
            """,
            (EMBEDDING_MODEL,),
        ).fetchall()

    return rows
```

`GROUP BY source` produces one result per filename; `count(*)` counts the stored
chunks in each group. `ORDER BY source` makes the output order predictable.
See [PostgreSQL grouping](https://www.postgresql.org/docs/17/queries-table-expressions.html#QUERIES-GROUP).

Read from PostgreSQL because that is what `/ask` searches. A new text file will
appear here only after its chunks have been built and imported. An empty table,
or no rows for this embedding model, produces an empty list.

## 2. Add the endpoint

In `knowledge_api.py`, extend the existing import:

```python
from pgvector_search import RetrievalUnavailable, list_sources
```

Add these models beside your existing response model:

```python
class SourceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    chunk_count: int = Field(gt=0)


class SourcesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: list[SourceSummary]
```

Then add this route:

```python
@app.get("/sources", response_model=SourcesResponse)
def sources():
    try:
        return {"sources": list_sources()}
    except (psycopg.Error, RetrievalUnavailable) as exc:
        raise HTTPException(503, "Document search is unavailable") from exc
```

FastAPI validates the returned data against the response model, as it does for
`/ask`. See [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/).

A successful query with no sources returns **200** and `{"sources": []}`.
A connection or configuration failure returns **503**. Neither path needs an
embedding or a generated answer.

## 3. Add four API test cases

Append this to `tests/test_knowledge_api.py`. Reuse its existing imports and
fixtures:

```python
@pytest.mark.parametrize("rows", [
    [
        {"source": "remote-work-policy.txt", "chunk_count": 1},
        {"source": "sample-policy.txt", "chunk_count": 3},
    ],
    [],
])
def test_sources_list(client, answerer, monkeypatch, rows):
    reader = Mock(return_value=rows)
    monkeypatch.setattr(knowledge_api, "list_sources", reader)

    response = client.get("/sources")

    assert response.status_code == 200
    assert response.json() == {"sources": rows}
    reader.assert_called_once_with()
    answerer.assert_not_called()


@pytest.mark.parametrize("error", [
    psycopg.OperationalError("private connection details"),
    RetrievalUnavailable("private setup details"),
])
def test_sources_failure(client, answerer, monkeypatch, error):
    reader = Mock(side_effect=error)
    monkeypatch.setattr(knowledge_api, "list_sources", reader)

    response = client.get("/sources")

    assert response.status_code == 503
    assert response.json() == {"detail": "Document search is unavailable"}
    reader.assert_called_once_with()
    answerer.assert_not_called()
```

Run:

```bash
source .venv/bin/activate
python -m pytest tests/test_knowledge_api.py -q
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check pgvector_search.py knowledge_api.py tests/test_knowledge_api.py
```

Expect **24 knowledge API tests**, **50 total tests**, and passing lint.
These four cases check the HTTP behavior with a fake database helper. They do
not execute the grouping query; the next step checks that query against your
stored collection.

## 4. Read the real collection

Start the database and API, or use your existing running services:

```bash
docker compose -f compose.knowledge.yml up -d --wait vector-db
uvicorn knowledge_api:app --host 127.0.0.1 --port 8001 --reload
```

Open <http://127.0.0.1:8001/docs> and execute **GET /sources**. Expect status 200:

```json
{
  "sources": [
    {"source": "remote-work-policy.txt", "chunk_count": 1},
    {"source": "sample-policy.txt", "chunk_count": 3}
  ]
}
```

That is **two sources and four chunks**. The filenames can be used as the
`source` value in `/ask`; no additional `/ask` request is required today.

## Done when

Send:

```text
Knowledge API tests passed: __
Total tests passed: __
Lint: pass/fail
GET /sources status: __
Remote-work chunk count: __
Sample-policy chunk count: __
Empty-list test status: __
Database-failure test status: __
Why read sources from PostgreSQL instead of listing the documents folder: __
```

Completed: reported 24 knowledge API tests, 50 total tests, and passing lint.
`GET /sources` returned 200 with one remote-work chunk and three sample-policy
chunks. Empty-list and database-failure tests returned 200 and 503 respectively.
Explained that PostgreSQL represents indexed content, while local files may
contain changes that have not been imported.

Next: [Day 41 — run the knowledge API in Docker](day-41.md).

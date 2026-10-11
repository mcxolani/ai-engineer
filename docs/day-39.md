# Day 39 — search within one source file

Today a caller can optionally choose which document `/ask` searches. Allow
30–40 minutes. The automated tests make no model calls. The three manual
requests normally use **three query embeddings and two generations**.

For example:

```json
{
  "question": "How many days per week can employees work remotely?",
  "source": "remote-work-policy.txt"
}
```

Omitting `source`, or sending `null`, searches all documents as before.

## 1. Apply the filter inside the SQL search

In `pgvector_search.py`, change the function definition to:

```python
def find_chunk(query, source=None):
```

Keep the existing check that the database has chunks for the embedding model.
Replace the later `row = connection.execute(...)` statement with:

```python
        row = connection.execute(
            """
            SELECT source, chunk_id, content,
                   1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE embedding_model = %s
              AND (%s::text IS NULL OR source = %s)
            ORDER BY embedding <=> %s::vector, source, chunk_id
            LIMIT 1
            """,
            (vector, EMBEDDING_MODEL, source, source, vector),
        ).fetchone()
```

When the parameter is `None`, the `IS NULL` condition allows every source.
Otherwise, `source = %s` restricts the candidates to the exact filename. Values
are still passed as SQL parameters.

Filtering happens before ranking and `LIMIT 1`. This lets PostgreSQL choose the
closest chunk **within the selected document**. Choosing one global winner first
and discarding it afterward could miss a useful chunk in the requested file.
See [PostgreSQL SELECT](https://www.postgresql.org/docs/17/sql-select.html).

Replace the existing `if row is None` block with:

```python
    if row is None:
        return None, None, response.usage.prompt_tokens
```

This means the query found no eligible rows, such as an unknown source filename.
The score is `None` because there was nothing to compare. If eligible rows exist
but their best score is below `0.30`, keep returning that numerical score with
no accepted chunk, as before.

In the command-line section, replace the `Top score` print with:

```python
    score_text = "none" if score is None else f"{score:.4f}"
    print(f"Top score: {score_text}")
```

## 2. Pass the source through the answer helper and API

In `ask_document.py`, change the function definition and retrieval call:

```python
def answer_question(question, source=None):
    question = question.strip()
    chunk, score, embedding_tokens = find_chunk(question, source=source)
```

Keep the rest of that function. Its existing no-match branch already skips
generation when `chunk` is `None`.

In `knowledge_api.py`, replace `QuestionRequest` with:

```python
class QuestionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    source: str | None = Field(default=None, min_length=1, max_length=255)
```

`default=None` makes the field optional. Strings are trimmed, and blank strings
are rejected. See [Pydantic fields](https://docs.pydantic.dev/latest/concepts/fields/).

In `AnswerResponse`, change the score field to allow a null score:

```python
    retrieval_score: float | None
```

In the `ask` route, replace the answer-helper call with:

```python
        return answer_question(request.question, source=request.source)
```

The existing exception handlers stay in place. An unavailable database still
returns 503. A successful search with no eligible rows is a normal 200 result.
This optional filter selects a document; it does not enforce user permissions.

## 3. Update and extend the API tests

First, update the four existing `answerer.assert_called_once_with(...)` assertions
in `tests/test_knowledge_api.py`. They now need the default source argument:

```python
    answerer.assert_called_once_with("support hours", source=None)
```

Use `"banana"` in the existing banana test. There are three existing assertions
for `"support hours"` and one for `"banana"`.

Then append these tests:

```python
@pytest.mark.parametrize("source", [" sample-policy.txt ", None])
def test_source_filter_is_forwarded(client, answerer, source):
    response = client.post("/ask", json={"question": "support hours", "source": source})
    assert response.status_code == 200
    expected_source = source.strip() if source is not None else None
    answerer.assert_called_once_with("support hours", source=expected_source)


@pytest.mark.parametrize("source", ["   ", 42, "x" * 256])
def test_invalid_source_skips_answerer(client, answerer, source):
    response = client.post("/ask", json={"question": "support hours", "source": source})
    assert response.status_code == 422
    answerer.assert_not_called()


def test_no_candidates_returns_null_score(client, answerer):
    answerer.return_value.update(
        answer="I couldn't find a suitable passage in the document.",
        source=None,
        chunk_id=None,
        retrieval_score=None,
        generation="skipped",
        generation_input_tokens=0,
        generation_output_tokens=0,
    )
    response = client.post(
        "/ask", json={"question": "support hours", "source": "missing-policy.txt"}
    )
    assert response.status_code == 200
    assert response.json() == answerer.return_value
    answerer.assert_called_once_with("support hours", source="missing-policy.txt")
```

Run:

```bash
source .venv/bin/activate
python -m pytest tests/test_knowledge_api.py -q
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check pgvector_search.py ask_document.py knowledge_api.py tests/test_knowledge_api.py
```

Expect **20 knowledge API tests**, **46 total tests**, and passing lint. The new
tests verify request handling and the response shape using a fake answer helper;
they do not execute the SQL filter.

## 4. Try three requests

Start the database and API, or let your existing API server reload:

```bash
docker compose -f compose.knowledge.yml up -d --wait vector-db
uvicorn knowledge_api:app --host 127.0.0.1 --port 8001 --reload
```

At <http://127.0.0.1:8001/docs>, submit the remote-work example from the top of
this lesson. Expect 200, source `remote-work-policy.txt`, chunk 1, and a supported
answer about up to two remote days per week with manager approval.

Then send an unfiltered question:

```json
{"question": "On which days and at what times is support available?"}
```

Expect 200, source `sample-policy.txt`, chunk 1, and the supported hours answer.

Finally, send a source filename that is not stored:

```json
{"question": "support hours", "source": "missing-policy.txt"}
```

Expect 200, null source/chunk/score, and skipped generation with zero generation
tokens. This version still embeds the question before executing the filtered
query, so the unknown-source request uses one embedding request.

The response's `source` identifies an accepted passage. It is not an echo of
the requested filter; if nothing is accepted, it remains null.

## Done when

Send:

```text
Knowledge API tests passed: __
Total tests passed: __
Lint: pass/fail
Filtered remote-work status / returned source: __ / __
Unfiltered hours returned source: __
Unknown-source status / score / generation: __ / __ / __
Why must the source filter run before LIMIT 1: __
```

Completed: reported 20 knowledge API tests, 46 total tests, and passing lint.
Confirmed the filtered remote-work response returned `remote-work-policy.txt`,
correcting a copied filename in the report. Unfiltered hours returned
`sample-policy.txt`; an unknown source returned 200 with a null score and skipped
generation. Explained that filtering must restrict candidates before choosing
the closest chunk.

Next: [Day 40 — list available sources](day-40.md).

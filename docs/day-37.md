# Day 37 — test the importer's checks

Today you will check that stale or incomplete cached data is rejected before
the importer connects to PostgreSQL. Allow 25–30 minutes.

These tests use temporary files and a fake connection function. **No running
database or model calls are needed.**

## 1. Add the tests

Create `tests/test_import_embeddings.py`:

```python
import json
from unittest.mock import Mock

import psycopg
import pytest

import import_embeddings as importer


@pytest.fixture
def prepared_import(tmp_path, monkeypatch):
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "practice.txt").write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
    (tmp_path / "data").mkdir()
    saved = {
        "model": "text-embedding-3-small",
        "chunks": [
            {
                "id": number,
                "source": "practice.txt",
                "text": text,
                "embedding": [1.0] + [0.0] * 1535,
            }
            for number, text in enumerate(
                ["First paragraph.", "Second paragraph."], start=1
            )
        ],
    }
    cache = tmp_path / "data" / "embeddings.json"
    cache.write_text(json.dumps(saved), encoding="utf-8")

    monkeypatch.setattr(importer, "__file__", str(tmp_path / "import_embeddings.py"))
    monkeypatch.setattr(importer, "load_dotenv", Mock())
    monkeypatch.setenv("KNOWLEDGE_DATABASE_URL", "postgresql://unused")
    connect = Mock(side_effect=psycopg.OperationalError("Stopped at test database boundary"))
    monkeypatch.setattr(importer.psycopg, "connect", connect)
    return saved, cache, connect


@pytest.mark.parametrize("change", ["edit", "delete", "add"])
def test_changed_documents_stop_before_database(prepared_import, tmp_path, change):
    _, _, connect = prepared_import
    document = tmp_path / "documents" / "practice.txt"
    if change == "edit":
        document.write_text("Changed paragraph.\n\nSecond paragraph.", encoding="utf-8")
    elif change == "delete":
        document.unlink()
    else:
        (document.parent / "extra.txt").write_text("An extra document.", encoding="utf-8")

    with pytest.raises(SystemExit, match="cache differs"):
        importer.main()
    connect.assert_not_called()


@pytest.mark.parametrize("problem,message", [
    ("missing_chunk", "cache differs"),
    ("empty", "no chunks"),
    ("dimensions", "1536 values"),
    ("model", "expects text-embedding-3-small"),
])
def test_invalid_cache_stops_before_database(prepared_import, problem, message):
    saved, cache, connect = prepared_import
    if problem == "missing_chunk":
        saved["chunks"].pop()
    elif problem == "empty":
        saved["chunks"] = []
    elif problem == "dimensions":
        saved["chunks"][0]["embedding"] = [1.0, 0.0]
    else:
        saved["model"] = "another-model"
    cache.write_text(json.dumps(saved), encoding="utf-8")

    with pytest.raises(SystemExit, match=message):
        importer.main()
    connect.assert_not_called()


def test_current_cache_reaches_database(prepared_import):
    _, _, connect = prepared_import
    with pytest.raises(psycopg.OperationalError, match="Stopped at test database boundary"):
        importer.main()
    connect.assert_called_once_with("postgresql://unused", connect_timeout=5)
```

## 2. Understand what is real and what is fake

The importer and document loader are real. They read actual files, but those
files live inside pytest's `tmp_path`, a separate temporary directory for each
test. Your project documents and cache are not edited. See
[pytest temporary directories](https://docs.pytest.org/en/stable/how-to/tmp_path.html).

Changing the importer's `__file__` makes its existing root-path calculation point
to that temporary directory. `monkeypatch` restores the changes after each test.
See [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html).

The connection function is fake and always raises a controlled error. This
prevents a real database connection even if a validation check breaks. The
vectors are invented test data with the expected length; no model generates them.

The last test expects that controlled connection error. It proves a current
cache gets past validation, so an importer that rejects every cache cannot pass
this suite. It does not prove the import itself succeeds.

## 3. Run the checks

From the project root:

```bash
source .venv/bin/activate
python -m pytest tests/test_import_embeddings.py -q
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check tests/test_import_embeddings.py
```

Expect **8 importer tests**, **40 total tests**, and passing lint.
The eight cases are three document changes, four invalid caches, and one current
cache that reaches the fake connection function.

## 4. Know what this does not prove

These tests verify checks that happen **before a database connection**. They
do not run SQL or prove PostgreSQL rollback. Day 36's manual exercise checked
successful cleanup; testing transaction failures against a real database is a
separate integration check.

A stale cache should stop the import. The normal fix is to rebuild from the
current documents, then import the refreshed cache. Do not bypass the comparison
to force old cached content into the database.

## Done when

Send:

```text
Importer tests passed: __
Total tests passed: __
Lint: pass/fail
Changed-document tests called the database: yes/no
Current-cache test reached the fake connection: yes/no
Project documents or cache changed by these tests: yes/no
Why don't these tests prove transaction rollback: __
```

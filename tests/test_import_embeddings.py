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

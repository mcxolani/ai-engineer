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

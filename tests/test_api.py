import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APITimeoutError, RateLimitError

from app import classifier, main
from app.classifier import ClassificationUnavailable, classify_message
from app.config import Settings
from app.schemas import Classification
from support_tools import ToolUnavailable


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "settings", Settings(_env_file=None, classifier_provider="demo"))
    with TestClient(main.app) as client:
        yield client


def test_demo_request(client):
    response = client.post("/tickets/classify", json={"message": "My payment went through twice"})
    assert response.status_code == 200
    assert response.headers["X-Classifier-Provider"] == "demo"
    assert response.json()["category"] == "billing"
    assert client.get("/health").json() == {"status": "ok", "provider": "demo"}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"message": "  "},
        {"message": "x" * 5001},
        {"message": 42},
        {"message": "Hi", "admin": True},
    ],
)
def test_invalid_input_never_calls_provider(client, monkeypatch, body):
    provider = AsyncMock()
    monkeypatch.setattr(main, "classify_message", provider)
    assert client.post("/tickets/classify", json=body).status_code == 422
    provider.assert_not_called()


@pytest.mark.parametrize(
    "error,status",
    [
        (ClassificationUnavailable("private provider details"), 502),
        (APITimeoutError(request=httpx.Request("POST", "https://example.test")), 504),
        (
            RateLimitError(
                "private provider details",
                response=httpx.Response(429, request=httpx.Request("POST", "https://example.test")),
                body=None,
            ),
            503,
        ),
    ],
)
def test_provider_failures_are_sanitized(client, monkeypatch, error, status):
    monkeypatch.setattr(main, "classify_message", AsyncMock(side_effect=error))
    response = client.post("/tickets/classify", json={"message": "Help"})
    assert response.status_code == status
    assert "private provider details" not in response.text


@pytest.mark.parametrize("status", ["completed", "incomplete"])
def test_missing_output_is_not_a_success(monkeypatch, status):
    sdk = SimpleNamespace(
        responses=SimpleNamespace(
            parse=AsyncMock(return_value=SimpleNamespace(status=status, output_parsed=None))
        )
    )
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=sdk)
    context.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(classifier, "AsyncOpenAI", lambda **kwargs: context)
    settings = Settings(_env_file=None, classifier_provider="openai", openai_api_key="test-key")
    with pytest.raises(ClassificationUnavailable):
        asyncio.run(classify_message("Help", settings))
    context.__aexit__.assert_awaited_once()


def test_live_adapter_passes_ticket_as_data_and_returns_parsed_output(monkeypatch):
    expected = Classification(
        category="account", priority="medium", sentiment="neutral", summary="Login fails."
    )
    parse = AsyncMock(return_value=SimpleNamespace(status="completed", output_parsed=expected))
    sdk = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=sdk)
    context.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(classifier, "AsyncOpenAI", lambda **kwargs: context)
    settings = Settings(_env_file=None, classifier_provider="openai", openai_api_key="test-key")
    result = asyncio.run(classify_message("I cannot log in", settings))
    context.__aexit__.assert_awaited_once()
    assert result == expected
    args = parse.call_args.kwargs
    assert args["input"][1] == {"role": "user", "content": "I cannot log in"}
    assert args["text_format"] is Classification
    assert args["store"] is False


def test_live_mode_requires_credentials():
    with pytest.raises(ValueError, match="Set OPENAI_API_KEY"):
        Settings(_env_file=None, classifier_provider="openai", openai_api_key="", database_url="")

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


@pytest.fixture
def assistant(client, monkeypatch):
    from pydantic import SecretStr
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
    from pydantic import SecretStr
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

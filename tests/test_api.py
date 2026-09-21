import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APITimeoutError, RateLimitError

from app.classifier import ClassificationUnavailable, OpenAIClassifier
from app.config import Settings
from app.main import create_app, get_classifier
from app.schemas import Classification


@pytest.fixture
def client():
    app = create_app(Settings(_env_file=None, classifier_provider="demo"))
    with TestClient(app) as client:
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
def test_invalid_input_never_calls_provider(client, body):
    provider = SimpleNamespace(classify=AsyncMock())
    client.app.dependency_overrides[get_classifier] = lambda: provider
    assert client.post("/tickets/classify", json=body).status_code == 422
    provider.classify.assert_not_called()


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
def test_provider_failures_are_sanitized(client, error, status):
    provider = SimpleNamespace(classify=AsyncMock(side_effect=error))
    client.app.dependency_overrides[get_classifier] = lambda: provider
    response = client.post("/tickets/classify", json={"message": "Help"})
    assert response.status_code == status
    assert "private provider details" not in response.text


@pytest.mark.parametrize("status", ["completed", "incomplete"])
def test_missing_output_is_not_a_success(status):
    sdk = SimpleNamespace(
        responses=SimpleNamespace(
            parse=AsyncMock(return_value=SimpleNamespace(status=status, output_parsed=None))
        )
    )
    with pytest.raises(ClassificationUnavailable):
        asyncio.run(OpenAIClassifier(sdk, "test-model").classify("Help"))


def test_live_adapter_passes_ticket_as_data_and_returns_parsed_output():
    expected = Classification(
        category="account", priority="medium", sentiment="neutral", summary="Login fails."
    )
    parse = AsyncMock(return_value=SimpleNamespace(status="completed", output_parsed=expected))
    sdk = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    result = asyncio.run(OpenAIClassifier(sdk, "test-model").classify("I cannot log in"))
    assert result == expected
    args = parse.call_args.kwargs
    assert args["input"][1] == {"role": "user", "content": "I cannot log in"}
    assert args["text_format"] is Classification
    assert args["store"] is False


def test_live_mode_requires_credentials():
    with pytest.raises(ValueError, match="Set OPENAI_API_KEY"):
        Settings(_env_file=None, classifier_provider="openai", openai_api_key="")

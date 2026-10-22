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

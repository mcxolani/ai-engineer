import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import execute_ticket_tool
from support_tools import ToolUnavailable


@pytest.fixture
def response():
    call = SimpleNamespace(
        type="function_call",
        name="lookup_ticket",
        arguments='{"ticket_id": 4}',
        call_id="call_test_4",
    )
    return SimpleNamespace(status="completed", output=[call])


@pytest.fixture
def lookup(monkeypatch):
    fake = AsyncMock()
    monkeypatch.setattr(execute_ticket_tool, "lookup_ticket", fake)
    return fake


@pytest.mark.parametrize("result", [
    {"status": "found", "ticket": {"id": 4}},
    {"status": "not_found", "ticket_id": 4},
])
def test_result_keeps_call_id(response, lookup, result):
    lookup.return_value = result
    output = asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))

    assert output["type"] == "function_call_output"
    assert output["call_id"] == "call_test_4"
    assert json.loads(output["output"]) == result
    lookup.assert_awaited_once_with({"ticket_id": 4}, "test-db")


@pytest.mark.parametrize("problem", ["incomplete", "missing", "multiple", "unknown"])
def test_invalid_response_skips_lookup(response, lookup, problem):
    if problem == "incomplete":
        response.status = "incomplete"
    elif problem == "missing":
        response.output = []
    elif problem == "multiple":
        response.output = response.output * 2
    else:
        response.output[0].name = "delete_ticket"

    with pytest.raises(ValueError):
        asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))
    lookup.assert_not_called()


def test_invalid_json_skips_lookup(response, lookup):
    response.output[0].arguments = "not JSON"
    with pytest.raises(json.JSONDecodeError):
        asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))
    lookup.assert_not_called()


def test_storage_failure_propagates(response, lookup):
    lookup.side_effect = ToolUnavailable("Ticket storage is unavailable")
    with pytest.raises(ToolUnavailable, match="Ticket storage is unavailable"):
        asyncio.run(execute_ticket_tool.execute_lookup(response, "test-db"))
    lookup.assert_awaited_once_with({"ticket_id": 4}, "test-db")

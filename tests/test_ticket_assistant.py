import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from openai.types.responses import ResponseFunctionToolCall

import ticket_assistant
from support_tools import ToolUnavailable


@pytest.fixture
def flow(monkeypatch):
    call = ResponseFunctionToolCall(
        type="function_call", name="lookup_ticket",
        arguments='{"ticket_id": 4}', call_id="call_test_4",
    )
    first = SimpleNamespace(status="completed", output=[call])
    tool_output = {
        "type": "function_call_output",
        "call_id": "call_test_4",
        "output": json.dumps({
            "status": "found",
            "ticket": {"id": 4, "result": {"category": "technical", "priority": "medium"}},
        }),
    }
    final = SimpleNamespace(
        status="completed", output=[],
        output_text="Ticket 4 is technical with medium priority.",
    )
    request = Mock(return_value=first)
    execute = AsyncMock(return_value=tool_output)
    create = Mock(return_value=final)
    context = MagicMock()
    context.__enter__.return_value.responses.create = create
    factory = Mock(return_value=context)
    monkeypatch.setenv("DATABASE_URL", "test-db")
    monkeypatch.setattr(ticket_assistant, "request_lookup", request)
    monkeypatch.setattr(ticket_assistant, "execute_lookup", execute)
    monkeypatch.setattr(ticket_assistant, "OpenAI", factory)
    return SimpleNamespace(
        first=first, tool_output=tool_output, final=final,
        request=request, execute=execute, create=create, factory=factory,
    )


def test_answer_receives_question_call_and_result(flow):
    question = "What category and priority are saved for ticket 4?"
    result = ticket_assistant.answer_ticket(question)

    flow.request.assert_called_once_with(question)
    flow.execute.assert_awaited_once_with(flow.first, "test-db")
    flow.create.assert_called_once()
    sent = flow.create.call_args.kwargs
    assert sent["input"] == [
        {"role": "user", "content": question},
        *flow.first.output,
        flow.tool_output,
    ]
    assert sent["tool_choice"] == "none"
    assert sent["store"] is False
    assert result["answer"] == flow.final.output_text
    assert result["call_id"] == "call_test_4"
    assert result["tool_result"] == json.loads(flow.tool_output["output"])


def test_not_found_is_forwarded(flow):
    missing = {"status": "not_found", "ticket_id": 4}
    flow.tool_output["output"] = json.dumps(missing)
    flow.final.output_text = "Ticket 4 was not found."

    result = ticket_assistant.answer_ticket("Look up ticket 4.")

    sent_output = flow.create.call_args.kwargs["input"][-1]
    assert json.loads(sent_output["output"]) == missing
    assert result["tool_result"] == missing
    assert result["answer"] == "Ticket 4 was not found."


@pytest.mark.parametrize("problem", ["incomplete", "blank", "another_call"])
def test_unusable_final_response_is_rejected(flow, problem):
    if problem == "incomplete":
        flow.final.status = "incomplete"
    elif problem == "blank":
        flow.final.output_text = "   "
    else:
        flow.final.output = [SimpleNamespace(type="function_call")]

    with pytest.raises(RuntimeError):
        ticket_assistant.answer_ticket("Look up ticket 4.")
    flow.execute.assert_awaited_once()
    flow.create.assert_called_once()


def test_lookup_failure_skips_second_model_request(flow):
    flow.execute.side_effect = ToolUnavailable("Ticket storage is unavailable")
    with pytest.raises(ToolUnavailable):
        ticket_assistant.answer_ticket("Look up ticket 4.")
    flow.request.assert_called_once()
    flow.factory.assert_not_called()

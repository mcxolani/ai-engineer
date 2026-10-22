import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from support_tools import TicketLookupArguments

TICKET_LOOKUP_TOOL = {
    "type": "function",
    "name": "lookup_ticket",
    "description": "Read a saved ticket classification by its ticket ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticket_id": {
                "type": "integer",
                "description": "The positive ID of the saved ticket to read.",
            },
        },
        "required": ["ticket_id"],
        "additionalProperties": False,
    },
    "strict": True,
}


def request_lookup(question):
    load_dotenv(Path(__file__).resolve().parent / ".env")
    with OpenAI(timeout=20.0, max_retries=0) as client:
        return client.responses.create(
            model="gpt-4o-mini",
            instructions="Request the ticket lookup using the ID in the question.",
            input=question,
            tools=[TICKET_LOOKUP_TOOL],
            tool_choice={"type": "function", "name": "lookup_ticket"},
            parallel_tool_calls=False,
            max_output_tokens=200,
            store=False,
        )


def main():
    response = request_lookup("Look up saved ticket 4.")
    if response.status != "completed":
        raise RuntimeError("The model response did not complete.")

    calls = [item for item in response.output if item.type == "function_call"]
    if len(calls) != 1 or calls[0].name != "lookup_ticket":
        raise RuntimeError("Expected one lookup_ticket request.")

    call = calls[0]
    arguments = TicketLookupArguments.model_validate_json(call.arguments)
    usage = response.usage
    print(json.dumps({
        "response_status": response.status,
        "tool_name": call.name,
        "call_id": call.call_id,
        "arguments": arguments.model_dump(),
        "tool_executed": False,
        "input_tokens": usage.input_tokens if usage is not None else None,
        "output_tokens": usage.output_tokens if usage is not None else None,
    }, indent=2))


if __name__ == "__main__":
    main()

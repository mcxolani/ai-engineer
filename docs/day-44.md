# Day 44 — inspect a model's tool request

Today, let the model request `lookup_ticket` and inspect what it returns.
Allow 20–30 minutes. Running the script once makes **one paid model request**.
It does not run the lookup or query PostgreSQL.

## 1. Describe the tool and request a call

Create `request_ticket_tool.py` in the project root:

```python
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
```

The tool definition describes a function; it does not send the function's Python
code to the model. We keep using `gpt-4o-mini`, which supports function calling.
See the [model documentation](https://developers.openai.com/api/docs/models/gpt-4o-mini).

`tool_choice` forces this particular function for the exercise. This does not
test whether the model can independently decide when a lookup is useful.
`parallel_tool_calls=False` limits the response to at most one function call.
`strict=True` asks for arguments matching the declared schema. See the
[OpenAI function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

We also validate the returned arguments locally with the Day 43 model. That
checks the positive ID range as well as the input type. Valid arguments do not
prove that a ticket exists.

## 2. Check import and lint first

```bash
source .venv/bin/activate
python -c "import request_ticket_tool; print('Import completed without a model call')"
ruff check request_ticket_tool.py
```

The main guard means importing the module does not send a request. This lesson
adds no pytest cases, so your existing suite remains at **60 tests**.

## 3. Run once and read the result

Use your existing `OPENAI_API_KEY` in `.env`, then run:

```bash
python request_ticket_tool.py
```

Expect these values, with a generated call ID and actual token counts:

```text
response_status: completed
tool_name: lookup_ticket
arguments: {"ticket_id": 4}
tool_executed: false
```

`call.arguments` arrives as a JSON string. The validation step parses it into
`TicketLookupArguments`. `call_id` identifies this particular request; later,
we will use it to associate the function's result with that request.

Notice that the result contains **no ticket category**. The model has requested
a lookup, but the application has not called `lookup_ticket`. Here, `completed`
means the model response finished, and `tool_executed: false` describes our
script's behavior. The database does not need to be running for this lesson.

## Done when

Send:

```text
Import without a model call: yes/no
Lint: pass/fail
Response status: __
Requested tool: __
Requested ticket ID: __
Call ID present: yes/no
Tool executed: true/false
Input / output tokens: __ / __
Does this response prove ticket 4 exists, and why: __
```

Completed: reported safe import, passing lint, completed response, a request for
`lookup_ticket` with ticket ID 4, a call ID, and usage of 87 input / 7 output
tokens. Correctly explained that the lookup had not run and ticket existence
was not established. The report's `Tool executed: true` contradicted that
explanation; inspected code confirms it prints `false` and never calls the tool.

Next: [Day 45 — execute the requested lookup](day-45.md).

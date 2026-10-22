import asyncio
import json
import os

from request_ticket_tool import request_lookup
from support_tools import lookup_ticket


async def execute_lookup(response, database_url):
    if response.status != "completed":
        raise ValueError("The model response did not complete.")

    calls = [item for item in response.output if item.type == "function_call"]
    if len(calls) != 1:
        raise ValueError("Expected exactly one function call.")

    call = calls[0]
    if call.name != "lookup_ticket":
        raise ValueError("Unsupported function name.")

    arguments = json.loads(call.arguments)
    result = await lookup_ticket(arguments, database_url)
    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": json.dumps(result),
    }


def main():
    response = request_lookup("Look up saved ticket 4.")
    output = asyncio.run(execute_lookup(response, os.getenv("DATABASE_URL", "")))
    print(f"Output type: {output['type']}")
    print(f"Call ID: {output['call_id']}")
    print(json.dumps(json.loads(output["output"]), indent=2))
    print("Result sent to model: no")


if __name__ == "__main__":
    main()

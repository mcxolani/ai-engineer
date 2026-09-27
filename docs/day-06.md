# Day 6: inspect token usage

Allow 15–20 minutes. You can now check answer quality and response time. Today
you will inspect how many tokens the model used for a request.

## 1. Read the usage numbers

The model API returns usage alongside its answer:

- `input_tokens`: tokens processed as input, including the instructions and ticket.
- `output_tokens`: tokens generated for the response.
- `total_tokens`: input plus output tokens.

Tokens are units of text, not a word count. Output usage can include tokens that
are not visible in the answer. See the official [token-counting guide](https://developers.openai.com/api/docs/guides/token-counting)
and [response usage reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create).

## 2. Print usage in the server terminal

Open `app/classifier.py`. Find the end of `await client.responses.parse(...)`.
Insert the following block **after that call and before the existing
`if response.status ...` check**. Use the same indentation as that check:

```python
        usage = getattr(response, "usage", None)
        if usage is not None:
            print(
                f"Tokens: input={usage.input_tokens}, "
                f"output={usage.output_tokens}, total={usage.total_tokens}",
                flush=True,
            )
        else:
            print("Tokens: usage unavailable", flush=True)
```

`getattr` reads the `usage` attribute, or gives `None` if it is absent. This also
works with our existing mocked responses in tests. Missing usage means unknown,
not zero. Leave the existing response-status check and return below this block.

This prints in the terminal running **uvicorn**, not the terminal running
`evaluate.py`. The model response exists inside the server's classifier function;
your endpoint still returns only the four classification fields.

## 3. Try one ticket, then your six cases

Restart the server and send the duplicate-payment example through
<http://127.0.0.1:8000/docs>:

```json
{"message": "My payment went through twice."}
```

Look for a line beginning `Tokens:` in the server terminal. Check that input plus
output equals total. Keep that line for your reply.

Then run your existing script from a second terminal:

```bash
source .venv/bin/activate
python evaluate.py
```

That makes six more paid classification requests. Watch the six new usage lines
in the server terminal. Compare them with the ticket order in your script.
Do not count the earlier manual request as part of this six-ticket run.

Also run `pytest -q` to check the application tests; those use mocked providers
and make no paid requests.

You're done when you can show usage for one ticket and explain why input usage
includes more than just the customer's message. Send:

```text
Score: __ / 6
Example ticket: My payment went through twice.
Input tokens: __
Output tokens: __
Total tokens: __
```

These are counts reported for returned responses, not a complete billing ledger
for retries or failed calls. Next session: use token counts to estimate cost.

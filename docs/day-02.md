# Day 2: get a real AI response

Allow 20–30 minutes. The AI connection is already written. Today you will enable
it and compare three answers.

## 1. Switch from demo to OpenAI

You need an OpenAI API key and available API credit/quota. If you need help getting
a key, follow the [official quickstart](https://developers.openai.com/api/docs/quickstart).
These calls send the ticket text to OpenAI and incur API usage charges.

In the project root, copy `.env.example` to `.env` **only if `.env` doesn't already
exist**. Edit `.env` so it contains:

```dotenv
CLASSIFIER_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Replace `your-key-here` with your key in that local file. Keep it out of chat and
source code. If your account cannot access this model, choose a compatible model
available to your account.

Stop the running server with Ctrl+C (or stop the VS Code debugger), then start it:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/health>. The `provider` should say `openai`.
This confirms the setting; the next step checks that a real call succeeds.

## 2. Try three tickets

At <http://127.0.0.1:8000/docs>, use `POST /tickets/classify`. Send each message
separately, using the same JSON shape as Day 1:

```json
{"message": "My payment went through twice"}
```

Our current prompt gives these expected labels:

| Message | Category | Priority | Sentiment |
| --- | --- | --- | --- |
| My payment went through twice | billing | high | neutral |
| I cannot log in to my account | account | medium | neutral |
| Thanks, your app is great! | general | low | positive |

Write down the returned labels and summaries. If an answer differs, record the
difference before changing anything. These are expectations, not measured results.

## 3. Understand the call

In `app/classifier.py`, find `client.responses.parse(...)`:

- `model` selects the AI model.
- `input` contains our instructions and the customer's message.
- `text_format=Classification` specifies the output fields.

This is [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs):
the response follows a schema. It can still make an incorrect classification.

You're done when all three requests succeed and you can explain one result using
the rules in `SYSTEM_PROMPT`. Share the three results and any unexpected answers.

If a call fails, share the HTTP status and error message, without credentials.
If you don't have a key yet, write your expected answers and read the call; leave
the live-call step pending. Set `CLASSIFIER_PROVIDER=demo` and restart to return
to the offline example.

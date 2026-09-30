# Day 28: add a question API

Allow 25–30 minutes. Today you will expose `answer_question` through FastAPI,
using the same request-validation ideas as Project 1.

## 1. Create the API

Create `knowledge_api.py` in the project root, beside `ask_document.py`:

```python
from typing import Literal

from fastapi import FastAPI, HTTPException
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ConfigDict, Field

from ask_document import answer_question

app = FastAPI(title="Document Knowledge Assistant")


class QuestionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=2000)


class AnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    source: str | None
    chunk_id: int | None = Field(gt=0)
    retrieval_score: float
    generation: Literal["completed", "skipped"]
    embedding_input_tokens: int = Field(ge=0)
    generation_input_tokens: int | None = Field(ge=0)
    generation_output_tokens: int | None = Field(ge=0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    try:
        return answer_question(request.question)
    except APITimeoutError as exc:
        raise HTTPException(504, "The model provider timed out") from exc
    except RateLimitError as exc:
        raise HTTPException(503, "The model provider is temporarily unavailable") from exc
    except FileNotFoundError as exc:
        raise HTTPException(503, "Build the document index before asking questions") from exc
    except (APIError, RuntimeError) as exc:
        raise HTTPException(502, "The model provider could not return a usable answer") from exc
```

`QuestionRequest` strips surrounding whitespace and rejects empty questions,
questions longer than 2,000 characters, and unexpected fields. These checks
happen before `answer_question` runs.

`AnswerResponse` checks the shape of the returned dictionary and documents it
in `/docs`. It does not check factual accuracy. See the
[FastAPI response-model guide](https://fastapi.tiangolo.com/tutorial/response-model/).

The endpoint uses ordinary `def` because the existing answer function makes
synchronous calls. FastAPI runs ordinary route functions in a worker thread.
See the [FastAPI concurrency guide](https://fastapi.tiangolo.com/async/#path-operation-functions).

## 2. Start the server

Run from the project root with your existing `.env` and saved document index:

```bash
source .venv/bin/activate
uvicorn knowledge_api:app --host 127.0.0.1 --port 8001 --reload
```

This starts Project 2 locally on port 8001. The Project 1 Docker configuration
serves the classifier on port 8000; use the command above for this lesson.

Open <http://127.0.0.1:8001/health>. Expect HTTP 200 and `{"status":"ok"}`.
This confirms the server responds; it does not test the saved index or model access.

## 3. Try four requests

Open <http://127.0.0.1:8001/docs>, expand `POST /ask`, and use **Try it out**.

First send:

```json
{"question": "On which days and at what times is support available?"}
```

Expect HTTP 200 with the hours answer, source `sample-policy.txt`, chunk 1,
and `generation: completed`. Read the answer against the passage as before.

Then send:

```json
{"question": "banana"}
```

Expect HTTP 200, a no-match answer, null source/chunk, and
`generation: skipped`. The request was processed successfully even though the
document did not yield an accepted passage.

Finally, try each invalid body:

```json
{"question": "   "}
```

```json
{}
```

Both should return HTTP 422 without calling the models. Opening `/docs` and
`/health` also makes no model requests. The two valid examples normally use
three paid requests in total: two embeddings and one generation.

The endpoint also maps missing-index errors to 503, provider timeouts to 504,
rate limits to 503, and other provider or incomplete-answer errors to 502.
We will add automated API checks in the next lesson.

## Done when

Send:

```text
GET /health status: __
POST /ask hours status: __
Hours source / chunk / generation: __ / __ / __
POST /ask banana status / generation: __ / __
Blank question status: __
Missing question status: __
Why does a no-match answer still return HTTP 200: __
```

Completed: reported HTTP 200 for health and both valid questions. The hours
response included `sample-policy.txt`, chunk 1, and completed generation;
`banana` skipped generation. Blank and missing questions returned 422.
Clarified that HTTP 200 means successful request processing, which can include
a valid no-match result.

Next: [Day 29 — test the question API](day-29.md).

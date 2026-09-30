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

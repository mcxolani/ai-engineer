from fastapi import FastAPI, HTTPException, Response
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from app.classifier import ClassificationUnavailable, classify_message
from app.config import Settings
from app.schemas import Classification, TicketRequest

app = FastAPI(
    title="Support Ticket Classifier",
    description="Demo mode returns a fixed example. Switch to OpenAI when ready.",
)
settings = Settings()


@app.get("/health")
def health():
    return {"status": "ok", "provider": settings.classifier_provider}


@app.post("/tickets/classify", response_model=Classification)
async def classify_ticket(ticket: TicketRequest, response: Response) -> Classification:
    response.headers["X-Classifier-Provider"] = settings.classifier_provider
    try:
        return await classify_message(ticket.message, settings)
    except APITimeoutError as exc:
        raise HTTPException(504, "The classification provider timed out") from exc
    except RateLimitError as exc:
        raise HTTPException(503, "The classification provider is temporarily unavailable") from exc
    except (APIError, ClassificationUnavailable, ValidationError) as exc:
        raise HTTPException(502, "The provider could not return a valid classification") from exc

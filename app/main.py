import psycopg
from fastapi import FastAPI, HTTPException, Response
from fastapi import Path
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from app.classifier import ClassificationUnavailable, classify_message
from app.config import Settings
from app.schemas import Classification, TicketRequest
from app.database import save_classification, get_classification
from app.schemas import SavedClassification

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
        result = await classify_message(ticket.message, settings)
        database_url = settings.database_url.get_secret_value()
        if database_url:
            saved_id = await save_classification(database_url, ticket.message, result)
            response.headers["X-Classification-ID"] = str(saved_id)
        return result

    except APITimeoutError as exc:
        raise HTTPException(504, "The classification provider timed out") from exc
    except RateLimitError as exc:
        raise HTTPException(503, "The classification provider is temporarily unavailable") from exc
    except (APIError, ClassificationUnavailable, ValidationError) as exc:
        raise HTTPException(502, "The provider could not return a valid classification") from exc
    except psycopg.Error as exc:
        raise HTTPException(503, "Could not save the classification") from exc


@app.get("/tickets/{classification_id}", response_model=SavedClassification)
async def read_ticket(
    classification_id: int = Path(gt=0, le=9223372036854775807),
) -> SavedClassification:
    database_url = settings.database_url.get_secret_value()
    if not database_url:
        raise HTTPException(503, "Database is not configured")
    try:
        saved = await get_classification(database_url, classification_id)
    except psycopg.Error as exc:
        raise HTTPException(503, "Could not read the classification") from exc

    if saved is None:
        raise HTTPException(404, "Classification not found")
    return saved

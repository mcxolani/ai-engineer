from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import ValidationError

from app.classifier import (
    ClassificationUnavailable,
    Classifier,
    DemoClassifier,
    OpenAIClassifier,
)
from app.config import Settings
from app.schemas import Classification, TicketRequest


def get_classifier(request: Request) -> Classifier:
    return request.app.state.classifier


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = settings or Settings()
        app.state.provider = config.classifier_provider
        if config.classifier_provider == "openai":
            async with AsyncOpenAI(
                api_key=config.openai_api_key.get_secret_value(), timeout=20.0, max_retries=2
            ) as client:
                app.state.classifier = OpenAIClassifier(client, config.openai_model)
                yield
        else:
            app.state.classifier = DemoClassifier()
            yield

    api = FastAPI(
        title="Support Ticket Classifier — Learning Lab",
        description="Day 1: typed requests and structured outputs. Demo mode returns a fixed example.",
        lifespan=lifespan,
    )

    @api.get("/health")
    async def health(request: Request):
        return {"status": "ok", "provider": request.app.state.provider}

    @api.post("/tickets/classify", response_model=Classification)
    async def classify_ticket(
        ticket: TicketRequest,
        request: Request,
        response: Response,
        classifier: Annotated[Classifier, Depends(get_classifier)],
    ) -> Classification:
        response.headers["X-Classifier-Provider"] = request.app.state.provider
        try:
            return await classifier.classify(ticket.message)
        except APITimeoutError as exc:
            raise HTTPException(504, "The classification provider timed out") from exc
        except RateLimitError as exc:
            raise HTTPException(
                503, "The classification provider is temporarily unavailable"
            ) from exc
        except (APIError, ClassificationUnavailable, ValidationError) as exc:
            raise HTTPException(
                502, "The provider could not return a valid classification"
            ) from exc

    return api


app = create_app()

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TicketRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message: str = Field(min_length=1, max_length=5000)


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["billing", "technical", "account", "general"]
    priority: Literal["low", "medium", "high"]
    sentiment: Literal["positive", "neutral", "frustrated"]
    summary: str = Field(min_length=1, max_length=300)


class SavedClassification(BaseModel):
    id: int
    message: str
    result: Classification
    created_at: datetime


class TicketAssistantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=2000)


class TicketAssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    ticket_id: int = Field(gt=0)
    tool_status: Literal["found", "not_found"]
    call_id: str = Field(min_length=1)
    generation: Literal["completed"]

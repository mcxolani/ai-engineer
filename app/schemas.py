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

import psycopg
from pydantic import BaseModel, ConfigDict, Field

from app.database import get_classification


class TicketLookupArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ticket_id: int = Field(gt=0, le=9223372036854775807)


class ToolUnavailable(RuntimeError):
    """The tool could not access its data source."""


async def lookup_ticket(arguments: dict, database_url: str) -> dict:
    args = TicketLookupArguments.model_validate(arguments)
    if not database_url:
        raise ToolUnavailable("Ticket storage is not configured")

    try:
        saved = await get_classification(database_url, args.ticket_id)
    except psycopg.Error as exc:
        raise ToolUnavailable("Ticket storage is unavailable") from exc

    if saved is None:
        return {"status": "not_found", "ticket_id": args.ticket_id}

    return {"status": "found", "ticket": saved.model_dump(mode="json")}

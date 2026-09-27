import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.schemas import Classification, SavedClassification


async def save_classification(
    database_url: str, message: str, result: Classification
) -> int:
    async with await psycopg.AsyncConnection.connect(
        database_url, connect_timeout=5
    ) as connection:
        cursor = await connection.execute(
            "INSERT INTO classifications (message, result) VALUES (%s, %s) RETURNING id",
            (message, Jsonb(result.model_dump())),
        )
        row = await cursor.fetchone()
        saved_id = row[0]

    return saved_id


async def get_classification(
    database_url: str, classification_id: int
) -> SavedClassification | None:
    async with await psycopg.AsyncConnection.connect(
        database_url, connect_timeout=5, row_factory=dict_row
    ) as connection:
        cursor = await connection.execute(
            "SELECT id, message, result, created_at FROM classifications WHERE id = %s",
            (classification_id,),
        )
        row = await cursor.fetchone()

    if row is None:
        return None
    return SavedClassification.model_validate(row)

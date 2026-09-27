import psycopg
from psycopg.types.json import Jsonb

from app.schemas import Classification


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


#     async def save_classification(
#         ^^^^^^^^^^^^^^^^^^^^^^^^^^
# TypeError: 'coroutine' object does not support the asynchronous context manager protocol
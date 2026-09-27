import os

import httpx
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from app.schemas import Classification

load_dotenv()
database_url = os.environ["DATABASE_URL"]
message = "I cannot log in to my account."

# Connect first, so an unavailable database fails before a paid model call.
with psycopg.connect(database_url, connect_timeout=5) as connection:
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=120) as client:
        health = client.get("/health")
        health.raise_for_status()
        if health.json()["provider"] != "openai":
            raise SystemExit("Switch to openai in .env and restart the API first.")

        response = client.post("/tickets/classify", json={"message": message})
        response.raise_for_status()
        result = Classification.model_validate(response.json())

    cursor = connection.execute(
        "INSERT INTO classifications (message, result) VALUES (%s, %s) RETURNING id",
        (message, Jsonb(result.model_dump())),
    )
    saved_id = cursor.fetchone()[0]

# The connection block has finished successfully, so the insert is committed.
print(f"Saved row ID: {saved_id}")
print(f"Category: {result.category}")

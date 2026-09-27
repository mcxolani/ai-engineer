# Day 9: save from Python

Allow 20–30 minutes. Today one script will call your existing API, save its
classification to PostgreSQL, and print the new row ID.

## 1. Add the database driver

In `pyproject.toml`, add these two entries inside the existing `dependencies` list:

```toml
  "psycopg[binary]>=3.2,<4",
  "python-dotenv>=1,<2",
```

From the project root, install the updated dependencies:

```bash
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Psycopg connects Python to PostgreSQL. `python-dotenv` loads settings from your
local `.env`. Add this line to `.env`, keeping the existing model settings:

```dotenv
DATABASE_URL=postgresql://ticket_app:local_learning_only@127.0.0.1:15432/tickets
```

These are the local learning credentials from your `compose.yml`. Keep `.env`
out of Git. The table from Day 8 must already exist.

## 2. Write the script

Create `save_ticket.py` beside `evaluate.py`:

```python
import os

import httpx
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from app.schemas import Classification

load_dotenv()
database_url = os.environ["DATABASE_URL"]
message = "My payment went through twice."

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
```

Three things to understand:

- `Classification.model_validate(...)` checks the API response before saving it.
- `Jsonb(...)` prepares the Python dictionary for the database's JSON column.
- `%s` placeholders pass values separately from SQL. Keep them unquoted and
  pass values in the second argument; don't build SQL with an f-string.

On normal exit, `with psycopg.connect(...)` commits and closes the connection.
If an exception escapes the block, the database transaction is rolled back.
See [Psycopg's basic usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html),
[query parameters](https://www.psycopg.org/psycopg3/docs/basic/params.html), and
[JSON adaptation](https://www.psycopg.org/psycopg3/docs/basic/adapt.html#json-adaptation).

## 3. Run and read back

Start the database with `docker compose up -d --wait db`. Keep the API running
in another terminal with `uvicorn app.main:app --reload`.

From your activated virtual environment, run:

```bash
python save_ticket.py
```

Each successful run makes one paid classification request and inserts one new
row. If saving fails after the model responds, that API usage has still occurred.
This script is the first persistence exercise; the API endpoint itself does not
save rows yet.

Check the saved row from a separate database connection. Replace `2` with the ID
printed by your script:

```bash
docker compose exec db psql -U ticket_app -d tickets -c "SELECT id, message, result->>'category' AS category FROM classifications WHERE id = 2;"
```

Then change `message` to `I cannot log in to my account.` and run the script once
more. Read back that row too; its expected category is `account`.

You're done when both rows are saved and read back. Send:

```text
Payment ticket row ID: __
Payment category read back: __
Login ticket row ID: __
Login category read back: __
```

Next session: move saving into the API so clients only need to send a ticket.

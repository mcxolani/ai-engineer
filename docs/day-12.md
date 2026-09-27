# Day 12: make database setup repeatable

Allow 20–30 minutes. The table currently exists because you created it by hand.
Today you will put that setup into a numbered SQL file and try it on both the
existing database and a new practice database. No model calls are needed.

## 1. Write the baseline migration

Create a `migrations` folder in the project root. Inside it, create
`001_create_classifications.sql`:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS classifications (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message text NOT NULL,
    result jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version)
VALUES ('001_create_classifications')
ON CONFLICT (version) DO NOTHING;
```

The first table records the migration version. The second defines your existing
classification table. `IF NOT EXISTS` skips a table that is already present;
`ON CONFLICT` avoids recording the same version twice.

This baseline matches the table we inspected in your database. `IF NOT EXISTS`
does not check or repair a different existing schema. Future changes belong in
new numbered files such as `002_...sql`, rather than edits to an applied file.
For now, you apply each file manually; the history table does not automatically
discover or run migrations.

## 2. Apply it to your current database

Start PostgreSQL if needed with `docker compose up -d --wait db`.
From the project root, record your existing row count:

```bash
docker compose exec -T db psql -U ticket_app -d tickets -c "SELECT count(*) FROM classifications;"
```

Then apply the file:

```bash
docker compose exec -T db psql -X -U ticket_app -d tickets --set=ON_ERROR_STOP=1 --single-transaction --file=- < migrations/001_create_classifications.sql
```

The shell reads your local SQL file and sends it into the container. `--file=-`
reads that input. `ON_ERROR_STOP` stops on an SQL error, and `--single-transaction`
applies all statements together or rolls them back on failure. These options are
documented in the [PostgreSQL psql manual](https://www.postgresql.org/docs/17/app-psql.html).

Run the exact same migration command a second time. Notices saying a table
already exists are expected. Then check:

```bash
docker compose exec -T db psql -U ticket_app -d tickets -c "SELECT version FROM schema_migrations;"
docker compose exec -T db psql -U ticket_app -d tickets -c "SELECT count(*) FROM classifications;"
```

There should be one version entry and the same ticket count as before. Avoid
submitting new POST requests during this comparison because they add rows.

## 3. Try a fresh database

Create a separate practice database, leaving your application database in place:

```bash
docker compose exec -T db createdb -U ticket_app tickets_practice
docker compose exec -T db psql -X -U ticket_app -d tickets_practice --set=ON_ERROR_STOP=1 --single-transaction --file=- < migrations/001_create_classifications.sql
docker compose exec -T db psql -U ticket_app -d tickets_practice -c "SELECT count(*) FROM classifications; SELECT version FROM schema_migrations;"
```

On a fresh database, expect zero classifications and one migration entry. If you
repeat this step later and `tickets_practice` already exists, skip `createdb` and
reuse it. Your `.env` should continue pointing to `tickets`, not `tickets_practice`.

Finally, confirm <http://127.0.0.1:8000/tickets/4> still returns the saved ticket
from your application database. Restart the API first if it is not running.

You're done when the same file sets up a fresh database and can be reapplied
without changing existing ticket data. Send:

```text
Migration version: __
Version entries after rerun: __
Existing ticket count before / after: __ / __
Practice database ticket count: __
GET /tickets/4 status: __
```

Next session: run the API alongside PostgreSQL with Docker Compose.

Completed: `001_create_classifications` recorded once after rerunning; existing
ticket count stayed 4/4; practice table contained zero tickets; `GET /tickets/4`
still returned 200.

Next: [Day 13 — run the app in Docker](day-13.md).

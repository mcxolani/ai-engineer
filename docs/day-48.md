# Day 48 — package the ticket assistant in Docker

The support API now imports ticket-assistant modules from the project root. Its
Docker image previously copied only `app/`, so the container needs those modules
as well. Today, update the image and verify it starts. Allow 20–30 minutes.
**No model calls are needed.**

## 1. Include the tool-flow modules in the image

In `Dockerfile`, add this line after `COPY app ./app`:

```dockerfile
COPY support_tools.py request_ticket_tool.py execute_ticket_tool.py ticket_assistant.py ./
```

The API imports `ticket_assistant`, which imports the other three modules. They
must therefore be present in `/app` when Uvicorn imports `app.main`.

Do not copy `.env`: the existing Compose service supplies environment variables
at runtime. The database URL in `compose.yml` remains the service address
`db:5432`, while your local scripts still use `127.0.0.1:15432`.

## 2. Run local checks

```bash
source .venv/bin/activate
CLASSIFIER_PROVIDER=demo OPENAI_API_KEY="" DATABASE_URL="" python -m pytest -q
ruff check .
```

Expect **85 total tests** and passing lint. Tests use fakes for model and
database behavior; no API key is required for them.

## 3. Build and start the container

```bash
docker compose config --quiet
docker compose up -d --build --wait api
docker compose ps
```

Expect both `db` and `api` to be healthy. A failed import would prevent the API
container from becoming healthy. If startup fails, inspect only the API logs:

```bash
docker compose logs --tail=50 api
```

Open <http://127.0.0.1:8000/docs> and run:

- `GET /health`: expect 200 and provider `demo` unless you configured another provider.
- `GET /tickets/4`: expect 200 and your earlier saved ticket, including category
  `technical` if ticket 4 remains unchanged.

Neither request invokes the ticket assistant or a model. `GET /tickets/4`
confirms the container can still read the existing database after the image
change.

## 4. Restart only the API

```bash
docker compose restart api
docker compose up -d --wait api
```

Run `GET /tickets/4` again. Expect the same saved row. The ticket database uses
a separate named volume, so recreating or restarting the API does not delete its
rows.

The new `POST /assistant/tickets/ask` endpoint is included in this image, but
do not call it today: it would run two paid model requests. This lesson proves
the container can import and host the code. The endpoint's behavior was already
checked locally and with fake helpers in Day 47.

## Done when

Send:

```text
Total tests passed: __
Lint: pass/fail
Compose configuration valid: yes/no
API container healthy: yes/no
Database container healthy: yes/no
GET /health status / provider: __ / __
GET /tickets/4 status / category: __ / __
GET /tickets/4 after API restart: __
Why must the Docker image copy the root tool modules: __
```

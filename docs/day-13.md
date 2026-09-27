# Day 13: run the app in Docker

Allow 25–35 minutes, plus the first image download/build. Today Docker Compose
will run both the API and PostgreSQL. Verification uses GET requests, so it makes
no model calls and adds no ticket rows.

## 1. Describe the API image

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This installs your package and runs Uvicorn inside the image. `0.0.0.0` lets the
server accept traffic arriving through the container's network interface. See
[FastAPI's container guide](https://fastapi.tiangolo.com/deployment/docker/).

Create `.dockerignore` beside it:

```text
.venv
.env
.env.*
.git
__pycache__
**/__pycache__
*.egg-info
.pytest_cache
.ruff_cache
```

These files stay out of the build context. The Dockerfile copies only the package
and its metadata; `.env` will be supplied at runtime.

## 2. Add the API service

In your existing `compose.yml`, add this under `services`, alongside `db`.
Keep the `db` service and `ticket_data` volume as they are:

```yaml
  api:
    build: .
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://ticket_app:local_learning_only@db:5432/tickets
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
```

Inside the container, `127.0.0.1` refers to that container itself. The service name
`db` reaches PostgreSQL on its internal port `5432`. Your host `.env` can keep
`127.0.0.1:15432`: the service's `environment` setting overrides that value inside
the API container. See [Compose networking](https://docs.docker.com/compose/how-tos/networking/).

`depends_on` waits for the database health check before starting the API. It does
not create tables or monitor database readiness on every request. The API health
check verifies that its HTTP endpoint responds; the GET test below checks database
access. See [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).

## 3. Start both services

Stop the Uvicorn process or VS Code debugger currently using port 8000. Keep
using the same project directory so Compose uses your existing database volume.

From the project root:

```bash
docker compose config --quiet
docker compose up -d --wait db
docker compose exec -T db psql -X -U ticket_app -d tickets --set=ON_ERROR_STOP=1 --single-transaction --file=- < migrations/001_create_classifications.sql
docker compose up -d --build --wait api
docker compose ps
```

The migration command also handles a fresh database. On your existing database,
its notices about existing tables are expected. Both services should be healthy.
If startup fails, use `docker compose logs api` or `docker compose logs db`.

## 4. Read your saved ticket

Open <http://127.0.0.1:8000/health> and <http://127.0.0.1:8000/tickets/4>.
Ticket 4 should still contain the photo-upload message and category `technical`.
The `/docs` page remains available too.

Restart only the API and repeat the GET:

```bash
docker compose restart api
docker compose up -d --wait api
```

Your existing `evaluate.py` still runs on the host against port 8000. You don't
need to run it for this lesson: it would make six model calls and save six rows.

After changing application code, use `docker compose up -d --build --wait api`
to rebuild it. A restart alone does not copy changed source into the image.
Use `docker compose stop` to stop both services while keeping the data.

Send:

```text
API container healthy: yes/no
Database container healthy: yes/no
GET /tickets/4 status: __
Category returned: __
GET /tickets/4 after API restart: __
```

You're done when the containerized API reads the same saved row before and after
restart. Next session: run the tests automatically in CI.

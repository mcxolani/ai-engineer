# Day 49 — check the ticket container in CI

Today, add a GitHub Actions workflow that builds the support API image, creates
a fresh ticket database schema, and checks HTTP behavior. Allow 20–30 minutes,
plus the workflow run. **No model calls or API secrets are needed.**

## 1. Create the workflow

Create `.github/workflows/ticket-container.yml`:

```yaml
name: Ticket container checks

on: [push, pull_request, workflow_dispatch]

permissions:
  contents: read

jobs:
  container:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    env:
      COMPOSE_PROJECT_NAME: ticket-ci
    steps:
      - uses: actions/checkout@v6

      - name: Create demo environment
        run: printf '%s\n' 'CLASSIFIER_PROVIDER=demo' 'OPENAI_API_KEY=' > .env

      - name: Validate Compose
        run: docker compose config --quiet

      - name: Build and start services
        run: docker compose up -d --build --wait --wait-timeout 90

      - name: Create database schema
        run: |
          docker compose exec -T db \
            psql -X -U ticket_app -d tickets \
            --set=ON_ERROR_STOP=1 --single-transaction --file=- \
            < migrations/001_create_classifications.sql

      - name: Check HTTP responses
        run: |
          python3 - <<'PY'
          import json
          import urllib.error
          import urllib.request

          with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
              assert response.status == 200
              assert json.load(response) == {"status": "ok", "provider": "demo"}
              print("/health: 200")

          try:
              urllib.request.urlopen("http://127.0.0.1:8000/tickets/999", timeout=5)
          except urllib.error.HTTPError as error:
              assert error.code == 404
              assert json.load(error) == {"detail": "Classification not found"}
              print("/tickets/999: 404")
          else:
              raise AssertionError("Expected a 404 for the empty CI database")
          PY

      - name: Show logs on failure
        if: failure()
        run: docker compose logs --no-color --tail=100

      - name: Remove CI containers and volume
        if: always()
        run: docker compose down --volumes
```

Workflow files belong in `.github/workflows/`. The workflow creates a disposable
`.env` for the runner so Compose gets demo mode without using your local file or
OpenAI key. See [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

`COMPOSE_PROJECT_NAME=ticket-ci` scopes container, network, and volume names to
this CI job. The cleanup step removes only that runner's project and volume.
It does not target your local Docker database.

## 2. Understand the 404 check

The fresh CI database has the `classifications` table after the migration but no
saved tickets. Therefore `GET /tickets/999` must return 404, not 200. That
checks the API can import the ticket-assistant modules, reach PostgreSQL, and
handle an empty collection without running the model.

The API is started after Compose sees a healthy database service. Its own health
endpoint only proves the server responds, which is why the second HTTP check
also reads from PostgreSQL. See [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).

## 3. Run it on GitHub

Review, commit, and push using your normal Git workflow. Include the updated
`Dockerfile` and new workflow. In GitHub's **Actions** tab, open **Ticket
container checks** for that commit.

Expect these lines in **Check HTTP responses**:

```text
/health: 200
/tickets/999: 404
```

Also check the existing **Python checks** workflow. It should still report 85
tests and passing lint. The separate knowledge-container workflow remains
independent of this ticket-container workflow.

## Done when

Send:

```text
GitHub Python lint: pass/fail
GitHub Python tests passed: __
Ticket container build/start: pass/fail
Schema step: pass/fail
CI /health status / provider: __ / __
CI /tickets/999 status / detail: __ / __
CI cleanup: pass/fail
Why is 404 correct for ticket 999 in CI: __
```

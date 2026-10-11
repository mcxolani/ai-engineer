# Day 42 — check the knowledge container in CI

Your Python tests pass, and the container works locally. Today, add a GitHub
Actions check that builds the image, creates a fresh database schema, and calls
the running API. Allow 20–30 minutes, plus the workflow run.

**No model calls or API secrets are needed.** This is a small integration check:
the real HTTP server talks to a real PostgreSQL database.

## 1. Add a workflow

Create `.github/workflows/knowledge-container.yml` with:

```yaml
name: Knowledge container checks

on: [push, pull_request, workflow_dispatch]

permissions:
  contents: read

jobs:
  container:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    env:
      OPENAI_API_KEY: ""
      COMPOSE_PROJECT_NAME: knowledge-ci
    steps:
      - uses: actions/checkout@v6

      - name: Validate Compose
        run: docker compose -f compose.knowledge.yml config --quiet

      - name: Build and start services
        run: docker compose -f compose.knowledge.yml up -d --build --wait --wait-timeout 90

      - name: Create database schema
        run: |
          docker compose -f compose.knowledge.yml exec -T vector-db \
            psql -X -U knowledge_app -d knowledge \
            --set=ON_ERROR_STOP=1 --single-transaction --file=- \
            < migrations/knowledge/001_create_document_chunks.sql

      - name: Check HTTP responses
        run: |
          python3 - <<'PY'
          import json
          import urllib.request

          expected = {
              "/health": {"status": "ok"},
              "/sources": {"sources": []},
          }
          for path, body in expected.items():
              with urllib.request.urlopen(
                  f"http://127.0.0.1:8001{path}", timeout=5
              ) as response:
                  actual = json.load(response)
                  assert response.status == 200, response.status
                  assert actual == body, actual
                  print(f"{path}: 200, {actual}")
          PY

      - name: Show logs on failure
        if: failure()
        run: docker compose -f compose.knowledge.yml logs --no-color --tail=100

      - name: Remove CI containers and volume
        if: always()
        run: docker compose -f compose.knowledge.yml down --volumes
```

Keep the existing `ci.yml` for lint and the 50 Python tests. This second workflow
checks the Docker build, startup, migration, and database access together.

The checkout action makes the repository files available to the job. Each
`run` step then executes on the runner; a failed command or Python assertion
fails its step. See [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
and [actions/checkout](https://github.com/actions/checkout).

## 2. Understand the empty result

GitHub's runner creates its own database. The migration creates the table, but
we do not import documents or generate embeddings. Therefore, `/sources` must
return:

```json
{"sources": []}
```

Your local database should still return its two sources and counts of 1 and 3.
The CI check runs in a separate environment and does not connect to that database.

The API health check can succeed before the table exists. Calling `/sources`
after applying the migration also checks the database connection and query.

`ON_ERROR_STOP=1` makes SQL errors fail the migration command. The final cleanup
step targets the disposable `knowledge-ci` project on the runner, including its
test volume. Keep that cleanup in the workflow; it is not an instruction to
remove your local learning database.

This check does **not** establish retrieval accuracy or answer quality. It does
not send `/ask` requests, and the database has no embedded passages.

## 3. Run it on GitHub

Review your changes and commit/push them using your normal Git workflow. Include
`Dockerfile.knowledge`, the updated `compose.knowledge.yml`, and the new workflow
if they have not already been committed.

In the repository's **Actions** tab, open **Knowledge container checks** for
your pushed commit. Expect the build, schema, and HTTP steps to pass. In **Check
HTTP responses**, look for:

```text
/health: 200, {'status': 'ok'}
/sources: 200, {'sources': []}
```

Also check that **Python checks** still passes lint and all 50 tests for the
same commit. If something fails, read the first failed step and its error; the
new workflow also prints container logs after a failure.

## Done when

Send:

```text
GitHub Python lint: pass/fail
GitHub Python tests passed: __
Knowledge container build/start: pass/fail
Schema step: pass/fail
CI /health status: __
CI /sources status / body: __ / __
CI cleanup: pass/fail
Why is an empty source list correct in CI but not expected in your local demo: __
```

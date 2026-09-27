# Support Ticket Classifier — project walkthrough

Draft for the Day 15 exercise. Complete the three prompts below in your own words.

## Problem

Write two sentences describing who would use this service and what work it helps
them do:

> This is the support service that helps the support team to be able to classify tickets logged by users. It needs to be validated heavly so that it does not classify to wrong category or sentiment or priority. What I would improve is maybe getting all tickets by day or classification and even by date

## How it works

```mermaid
flowchart LR
    A[POST ticket] --> B[FastAPI input validation]
    B --> C[Model classification]
    C --> D[Validated classification]
    D --> E[PostgreSQL save when configured]
    E --> F[JSON response and saved ID header]
    G[GET saved ID] --> H[PostgreSQL read]
    H --> I[Saved ticket response]
```

The live provider returns `category`, `priority`, `sentiment`, and `summary`.
The offline demo returns a fixed example. The API uses async calls for both the
model and PostgreSQL. Database saving is enabled by `DATABASE_URL`; Compose
configures it for the containerized service.

Saved rows contain the message, classification JSON, ID, and creation time.
A GET request reads the saved result without generating another answer.

Explain why validation matters, and give an example of an answer that has valid
fields but the wrong classification:

> Your explanation here.

## Evidence collected while building

| Check | Recorded result | Scope |
| --- | --- | --- |
| Label evaluation | 6/6 in the reported run | Six development examples; the prompt was tuned using this small set |
| Request timing | 1.31s average, 1.91s slowest | Six-ticket baseline from Day 5, before database saving was added |
| Token usage | 277 input + 29 output = 306 | One duplicate-payment response, not the total evaluation run |
| Automated tests | 18 passing | Input validation, provider handling, and mocked persistence/read behavior |
| Persistence | Saved rows read back after restart | Manually verified against PostgreSQL |
| Schema setup | Migration reapplied; 4 rows preserved | Also applied to a fresh practice database |
| Containers | Both healthy; saved ticket readable after API restart | Local Docker Compose deployment |
| CI | Lint and tests passing | Reported GitHub Actions run |

These checks establish a working learning project. They do not establish accuracy
on a large independent dataset or production performance under load.

## Current limits and next improvement

The service currently has no authentication or request deduplication. If model
classification succeeds and saving fails, model usage has still occurred. Usage
is printed to the server terminal rather than stored as a billing record. The
migration is a manually applied baseline; CI currently uses mocked dependencies.

Choose one improvement and explain the concrete problem it would address:

> Your explanation here.

## Run and demonstrate

See the [README](../README.md) for setup, [Day 13](day-13.md) for the container
commands, and [Day 15](day-15.md) for the short save/read demonstration.

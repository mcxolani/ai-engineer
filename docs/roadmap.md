# Build milestones

Use the supplied roadmap as a direction, with these concrete checkpoints.
The schedule can stretch around your available time.

| Phase | Deliverable | Completion evidence |
| --- | --- | --- |
| Weeks 1–2: Python + model APIs | Support ticket classifier | Validated outputs, failure handling, saved tickets in PostgreSQL, Docker run, tests, token usage records |
| Weeks 3–4: RAG | Company knowledge assistant | Ingest documents, retrieve with pgvector, answer with traceable sources, evaluate a small question set |
| Week 5: tools | Customer support tools | Validated tool arguments, explicit execution permissions, tested failures |
| Weeks 6–7: agents | Business operations workflow | LangGraph state, checkpoints, bounded execution, approval before external actions |
| Week 8: MCP | Expose business tools | Agent connects to an MCP server and uses constrained tools |
| Week 9: evaluation | Regression suite | Versioned dataset and repeatable quality measurements |
| Week 10: security + observability | Inspectable service | Traces, injection test cases, access controls, usage limits |
| Weeks 11–12: production + portfolio | Deployable projects | CI, deployment documentation, architecture walkthrough, demo and measured limitations |

## Project 1 increments

- [x] Runnable FastAPI starter with typed input and output.
- [x] Explicit offline demo and optional OpenAI adapter.
- [x] Local tests for invalid inputs and provider failures.
- [x] Complete the 20-minute Day 1 exercise and explain the flow (completed 2026-09-23).
- [x] Complete [Day 2](day-02.md): verify real API access and compare three examples (reported complete).
- [ ] Complete [Day 3](day-03.md): score five tickets and investigate one result.
- [ ] Record latency and token usage; calculate cost using configured prices.
- [ ] Save classifications to PostgreSQL and add migrations.
- [ ] Package API and database with Docker Compose.
- [ ] Add CI and a short architecture/demo write-up.

Each increment should leave a working service. Start portfolio and interview notes
as you build; begin applications once you can demonstrate a useful, tested project.

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
- [x] Complete [Day 3](day-03.md): score five tickets and investigate one result (rerun reported as 5/5).
- [x] Complete [Day 4](day-04.md): calculate the score with a Python script (six results supplied, 6/6).
- [x] Complete [Day 5](day-05.md): corrected run reported 6/6, average 1.31 seconds, slowest 1.91 seconds.
- [x] Complete [Day 6](day-06.md): reported 6/6; example usage 277 input + 29 output = 306 tokens.
- [x] Complete [Day 7](day-07.md): all four cost calculations correct; explained the unchanged input cost.
- [x] Complete [Day 8](day-08.md): healthy database; row 1 read back as billing and survived a restart.
- [x] Complete [Day 9](day-09.md): payment row 2 read back as billing; login row 3 as account.
- [x] Complete [Day 10](day-10.md): 15 tests passed; HTTP 200 with saved ID 4; verified technical ticket in PostgreSQL.
- [x] Complete [Day 11](day-11.md): 18 tests passed; saved row 200/technical, missing ID 404, invalid ID 422.
- [x] Complete [Day 12](day-12.md): version 001 recorded once; ticket count stayed 4/4; practice table empty; saved ticket still returns 200.
- [x] Complete [Day 13](day-13.md): both containers healthy; ticket 4 returned 200/technical before and after API restart.
- [x] Complete [Day 14](day-14.md): lint and 18 tests passed locally; GitHub Actions lint and tests reported passing.
- [x] Complete [Day 15](day-15.md): walkthrough, README update, and save/read demonstration reported complete.

### Project 1 backlog

- [ ] List saved tickets through `GET /tickets`, with category and date filters
  and pagination. Selected as the next improvement during the walkthrough.

## Project 2 increments

- [x] Complete [Day 16](day-16.md): reported three chunks from `sample-policy.txt`,
  correctly selected chunk 3 for sign-in, and explained source tracking.
- [x] Complete [Day 17](day-17.md): reported correct results for three keyword
  searches and the no-match case; clarified whole-word matching.
- [x] Complete [Day 18](day-18.md): interactive search works; reported 4/5,
  with `login` returning `None` instead of chunk 3. Clarified whole-word matching.
- [x] Complete [Day 19](day-19.md): reported 1,536 dimensions and 8 input tokens
  using `text-embedding-3-small`; correctly explained dimensions.
- [x] Complete [Day 20](day-20.md): reported similarities 1, 0.6345, and 0.2302;
  correctly identified related wording and distinguished similarity from confidence.
- [x] Complete [Day 21](day-21.md): reported `login` retrieving chunk 3 at 0.3423;
  `banana` retrieved irrelevant chunk 2, revealing the need for a no-match rule.
- [x] Complete [Day 22](day-22.md): trial minimum 0.30 accepted `login` at 0.3423
  and `support hours` at 0.5717; rejected `banana` at 0.0620. Explained the tradeoff.
- [x] Complete [Day 23](day-23.md): reported three saved 1,536-value vectors,
  one query vector per search, correct `login` result, and no match for `banana`
  after restarting. Explained the reduction in input tokens.
- [x] Complete [Day 24](day-24.md): reported 5/5 and 8 query input tokens,
  improving on the keyword baseline's 4/5; import safe and dataset limits understood.
- [x] Complete [Day 25](day-25.md): source shown for password guidance; `banana`
  skipped generation; expiry question scored 0.3743 and generation correctly
  reported missing information. Recorded an unsupported addition in the password answer.
- [x] Complete [Day 26](day-26.md): recorded answers reviewed as 4/4, with no
  unsupported additions. Both missing-information cases completed generation
  and correctly declined to supply an answer.
- [x] Complete [Day 27](day-27.md): reported safe import, supported hours answer
  with source/chunk metadata, and null source/chunk with zero generation tokens
  for `banana`. Explained reuse by API callers.
- [ ] Complete [Day 28](day-28.md): serve the knowledge assistant through
  `POST /ask`, with typed request/response data and invalid-input rejection.

Each increment should leave a working service. Start portfolio and interview notes
as you build; begin applications once you can demonstrate a useful, tested project.

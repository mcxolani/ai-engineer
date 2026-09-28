# Day 15: explain and demonstrate your project

Allow 20–30 minutes. This is the final Project 1 lesson. You have a working
classifier, persistence, evaluation script, containers, and CI. Today you will
make it easy for someone else to understand what you built.

## 1. Finish the walkthrough

Open [project-01.md](project-01.md). The implemented features and recorded results
are filled in. Complete the three prompts in your own words:

1. What problem does this solve?
2. Why does the output need validation?
3. What would you improve next, and why?

Explain it as if another backend engineer has never seen the code. Keep the whole
walkthrough short enough to read in a few minutes.

## 2. Make the README useful to a new reader

At the top of `README.md`, write two or three sentences describing the project
and link to the walkthrough:

```markdown
[Project walkthrough](docs/project-01.md)
```

Update its setup instructions to include the Docker path you have tested:

- Create `.env` from `.env.example` only if it does not already exist. Demo mode
  needs no key; real classification needs the OpenAI settings from Day 2.
- Start PostgreSQL, apply the migration, then build and start the API, using the
  commands from [Day 13](day-13.md).
- Open `/docs` and explain the POST and GET endpoints.
- Explain that `DATABASE_URL` enables saving. Compose supplies it automatically.

Keep the local Python setup as an alternative. A fresh installation has no ticket
4: tell new readers to use the ID returned by their own POST request.

## 3. Rehearse a three-minute demo

Use the running containerized app:

1. Show `/health` and name the active provider. Demo mode returns a fixed answer;
   use `openai` if you want to demonstrate real classification.
2. Send a ticket through `POST /tickets/classify` in `/docs`.
3. Explain the four output fields and note `X-Classification-ID`.
4. Retrieve that same ID with `GET /tickets/{classification_id}`.
5. Show the passing GitHub Actions job and your six-case evaluation script.

One live POST makes a paid model request and saves one row. The GET reads that
row without calling the model. You can show the evaluation script without
running six additional requests. Recording a video is optional.

Be ready to explain why a 6/6 label score is different from passing 18 application
tests. Also explain why a schema-valid answer can still be wrong.

## Done when

- The walkthrough is in your own words and linked from the README.
- A reader can find setup steps, the two endpoints, and the project's limitations.
- You can demonstrate one saved classification and retrieve it by ID.

Send:

```text
Walkthrough completed: yes/no
README updated: yes/no
Save/read demo completed: yes/no
One improvement I would make next: __
```

After this, we will start Project 2: a document knowledge assistant, beginning
with loading and splitting a small text document.

Completed: walkthrough, README update, and save/read demo reported done.
Chosen improvement: list saved tickets with filters.

Next: [Day 16 — load and split a document](day-16.md).

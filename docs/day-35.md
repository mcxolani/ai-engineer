# Day 35 — explain your knowledge assistant

Today is a short checkpoint: explain what you built and document how to run it.
Allow 15–20 minutes. No model calls or API credit are needed for this lesson.

## 1. Walk through the two flows

Open the [project walkthrough](project-02.md). Follow the file links and explain
these two flows aloud in your own words:

- **Preparing documents:** text files → paragraph chunks → embeddings → JSON
  cache → PostgreSQL.
- **Answering questions:** HTTP request → validation → query embedding → SQL
  search → threshold decision → generation or no match.

Point to where each step happens in the code. Then explain why the filename
and chunk number must travel together.

Use your recorded Day 34 results; you do not need to submit new API questions.

## 2. Read the two chunk-1 passages

From the project root, run:

```bash
docker compose -f compose.knowledge.yml up -d --wait vector-db
docker compose -f compose.knowledge.yml exec -T vector-db psql -X -U knowledge_app -d knowledge --set=ON_ERROR_STOP=1 -c "SELECT source, chunk_id, content FROM document_chunks WHERE chunk_id = 1 ORDER BY source;"
```

Expect two rows: remote-work guidance from `remote-work-policy.txt` and support
hours from `sample-policy.txt`. These are the passages identified by your two
successful API responses. Reading them directly makes no model requests.

## 3. Add Project 2 to the README

Add a **Knowledge assistant** section to `README.md`, in your own words.
Include:

- What the assistant does, with a link to `docs/project-02.md`.
- How to start its database and API on port 8001; the walkthrough has the commands.
- The required environment-variable names: `OPENAI_API_KEY` and
  `KNOWLEDGE_DATABASE_URL`. Include setup links for the migration and document import.
- The reported retrieval result of **6/6**, clearly described as six development
  queries, and the fact that live questions incur model usage.

If `.env.example` does not yet contain `KNOWLEDGE_DATABASE_URL=`, add that empty
setting on its own line. Keep your actual connection value and API key in `.env`.

## 4. Choose one next improvement

In the walkthrough's final section, replace the placeholder with one improvement
and a sentence explaining why it matters. For example:

- Remove obsolete database chunks when a document changes.
- Let callers limit their search to a specific source file.
- Read PDF documents as well as text files.

Finally, change the walkthrough's opening status to say the Day 35 walkthrough
is complete. This records this checkpoint; it does not claim the later features
are already implemented.

## Done when

Send:

```text
Both flows explained: yes/no
Both chunk-1 passages read back: yes/no
README updated: yes/no
Walkthrough updated: yes/no
Why doesn't editing a text file immediately change API answers: __
One improvement I would make next, and why: __
```

Completed: both flows explained, both passages read, and README/walkthrough
updates reported complete. Correctly explained that indexing is not automatic.
Selected cleanup of database rows for removed documents or chunks as the next
improvement; the next lesson places that cleanup in the import transaction.

Next: [Day 36 — remove obsolete database chunks](day-36.md).

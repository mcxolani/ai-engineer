# Day 26: check answer quality

Allow 15–20 minutes. Your retrieval evaluation scored 5/5, but a generated answer
still added a detail that the passage did not state. Today you will check the
answers themselves using four new questions.

## 1. Read the scoring rule

Open [answer-evaluation.md](answer-evaluation.md). It contains four questions,
the expected behavior, and space to record the results.

Give each case **PASS** only when:

- An answerable question gets the required information from the correct passage,
  with the correct source label and no unsupported factual additions.
- An unanswerable question gets an explicit missing-information or no-match
  response, without inventing an answer.

Otherwise, give it **FAIL** and explain the reason. Different wording is fine;
compare the meaning with the [sample document](../documents/sample-policy.txt).
A correct main point with an invented extra detail still fails this strict check.

`Generation: completed` means a model response arrived. It does not mean that
the answer is correct. A completed missing-information response can be a pass.
For an unanswerable question, skipped generation can also pass, but it tests
the retrieval cutoff rather than the model's ability to admit missing information.

## 2. Run the four questions

Keep the current prompt, saved document, models, and 0.30 cutoff while collecting
this first set of results. Run the following once for each question in the
evaluation file:

```bash
source .venv/bin/activate
python ask_document.py
```

Copy the actual answer, score, source, and generation status into the file.
When generation is skipped, record the source as `none`.

These four runs make four query-embedding requests and up to four generation
requests: **up to eight paid requests total**. There is no need to rebuild the
document vectors. If an API error interrupts a case, record `ERROR` and resolve
it before reporting a complete score; it is not a no-match result.

## 3. Review and count

Read each answer beside its expected behavior and mark PASS or FAIL. Count one
point per passing case. Keep the first results, including failures, so we can
decide what needs improving from evidence.

Pay particular attention to invented timezones, refund promises, and URLs.
Those details are absent from the document.

These questions were not used to choose the current cutoff or prompt. That
makes them a useful next check, though four cases are still a small sample.
If you later tune the system using them, treat them as development examples and
reserve additional new questions for an independent check.

## Done when

Fill in [answer-evaluation.md](answer-evaluation.md), then send:

```text
Answer quality score: __/4
Case 1 — support hours: PASS/FAIL
Case 2 — payment reference: PASS/FAIL
Case 3 — refund timing: PASS/FAIL
Case 4 — reset URL: PASS/FAIL
Unsupported details found: __
Why can retrieval pass while the answer fails: __
```

Completed: all four answers recorded in [answer-evaluation.md](answer-evaluation.md)
were reviewed against the source and passed. Support hours and payment reference
were correct; refund timing and reset URL correctly reported missing information.
No unsupported additions were found in these four answers.

Next: [Day 27 — return answers as data](day-27.md).

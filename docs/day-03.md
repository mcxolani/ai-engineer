# Day 3: check the answers

Allow 20–30 minutes. Today you will measure how well the classifier follows our
rules. You can use the existing app; no new packages are needed.

## 1. Make five predictions

Open [the results worksheet](day-03-results.md). It has five tickets and expected
labels based on `SYSTEM_PROMPT` in `app/classifier.py`.

Read the tickets and the prompt before making any calls. Explain to yourself why
each expected label fits. For example, a duplicate payment is urgent, but the
customer's words do not necessarily express frustration.

These expected answers are your small **evaluation dataset**: examples you can
reuse to check whether a change helps.

## 2. Run and score

Start the app as in Day 2. Check <http://127.0.0.1:8000/health> says `openai`.
Then send each worksheet message through `POST /tickets/classify` at
<http://127.0.0.1:8000/docs>. These are five paid model requests.

For each ticket, record the returned category, priority, sentiment, and summary.
Count a ticket as correct only when **all three labels** match the expected ones.
Count failed requests as unsuccessful too, and note the error separately.

```text
Score = correct tickets / 5
Example: 4 / 5 = 80%
```

Also read every summary. Does it add a fact the customer never mentioned?
Record that separately: the label score does not measure summary quality.

## 3. Investigate one result

Pick one wrong or surprising answer. Find the prompt rule that should control it.
Write one sentence explaining what went wrong.

If a rule is unclear, edit just that rule in `SYSTEM_PROMPT`. Restart the server,
run the same five tickets again, and record the second score. Keep the expected
answers fixed so you can compare the runs fairly. The rerun makes five more paid
requests. Keep a copy of the old prompt so you can undo the change.

If all five are correct, leave the prompt alone. Instead, write a sixth, harder
ticket and its expected labels before testing it. Record that separately from
the original five-ticket score.

A perfect score on five examples does not establish general accuracy. Likewise,
one better run does not prove the prompt improved: model answers can vary.

You're done when the worksheet contains five results, a score, and one observation.
Share those with me. Next: [Day 4 — automate the check](day-04.md).

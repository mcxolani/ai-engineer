# Day 22: allow a no-match result

Allow 15–20 minutes. Your search found the right chunk for `login`, but it also
returned an irrelevant chunk for `banana`. Today you will add a simple rule:
only accept the top chunk if its score reaches a minimum value.

## 1. Add the rule

In `semantic_search.py`, keep everything above
`best_score, best_chunk = ranked[0]`. Replace that line and everything below it
with:

```python
minimum_score = 0.30
best_score, best_chunk = ranked[0]

print(f"\nTop candidate: {best_chunk['id']}")
print(f"Top score: {best_score:.4f}")
print(f"Minimum score: {minimum_score:.2f}")

if best_score >= minimum_score:
    print(f"Result: accepted chunk {best_chunk['id']}")
    print(f"Source: {best_chunk['source']}")
    print(best_chunk["text"])
else:
    print("Result: no match above the minimum score.")

print(f"Input tokens: {response.usage.prompt_tokens}")
```

`0.30` is a **trial value for this exercise**, chosen below your observed
`login` score of 0.3423. We have not established that it separates relevant
and irrelevant results. It is not a universal cutoff or a confidence percentage.

The earlier ranking lines still show all candidates for inspection. The final
`Result:` line now tells you whether the best candidate was accepted.

## 2. Check three searches

Run the script once for each query below:

```bash
source .venv/bin/activate
python semantic_search.py
```

| Query | Desired result | Record |
| --- | --- | --- |
| `login` | Accept chunk 3 | Top score and final result |
| `banana` | No match | Top score and final result |
| `support hours` | Accept chunk 1 | Top score and final result |

These three runs make three paid requests. Each request still embeds the
query and the three document chunks, as in Day 21.

Record what actually happens. If `banana` is accepted, or a relevant query is
rejected, that is useful evidence about this trial value. Keep it at 0.30 for
this first report so we can assess the results together.

The code compares the full score; `.4f` only rounds what you see on screen.

## 3. Understand the tradeoff

A higher minimum rejects more candidates. That can remove irrelevant results,
but it can also reject a useful chunk. A lower minimum accepts more candidates,
including potentially irrelevant ones.

Passing the rule does not prove that the chunk answers the question. A no-match
result means nothing passed this rule; it does not prove the document has no
relevant information. We need more labeled examples, including new ones we have
not used to choose the cutoff, before trusting it broadly.

## Done when

Send:

```text
Minimum score: __
login → top score / result: __ / __
banana → top score / result: __ / __
support hours → top score / result: __ / __
Why can raising the minimum reject a useful chunk: __
```

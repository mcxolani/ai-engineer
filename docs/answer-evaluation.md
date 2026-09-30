# Answer quality evaluation — Day 26

Status: completed. The four recorded answers were reviewed against the sample
document and satisfy the rubric: 4/4, with no unsupported additions found.
Use the rubric in [Day 26](day-26.md) and the
[sample document](../documents/sample-policy.txt).

Settings for this run: retrieval cutoff 0.30, embeddings `text-embedding-3-small`,
generation `gpt-4o-mini`, existing saved document vectors.

## Case 1: support hours

Question: **On which days and at what times is support available?**

Expected: Monday to Friday, 09:00–17:00, supported by chunk 1. The document does
not specify a timezone. It also permits mentioning that messages outside those
hours are reviewed on the next working day.

- Retrieval score: 0.6099
- Retrieved source and chunk (or none): sample-policy.txt (chunk 1)
- Generation (completed/skipped): completed
- Actual answer: Support is available Monday to Friday, from 09:00 to 17:00.
- Verdict (PASS/FAIL/ERROR): PASS
- Reason: it did get the right days and times and the chuck states those

## Case 2: payment reference

Question: **What information should I provide when reporting a duplicate payment?**

Expected: the payment reference, supported by chunk 2. The team checks the
billing records; the passage does not require the customer to supply those
records, card details, or screenshots.

- Retrieval score: 0.6785
- Retrieved source and chunk (or none): sample-policy.txt (chunk 2)
- Generation (completed/skipped): completed
- Actual answer: You should provide the payment reference when reporting a duplicate payment.
- Verdict (PASS/FAIL/ERROR): PASS
- Reason: it provided the answer that matches the chunk 2

## Case 3: refund timing

Question: **How many days does a duplicate-payment refund take?**

Expected: acknowledge that the document does not provide the timeframe, or
return no match. Even if chunk 2 is retrieved, it gives no refund timeline
and does not guarantee a refund.

- Retrieval score: 0.5084
- Retrieved source and chunk (or none): sample-policy.txt (chunk 2)
- Generation (completed/skipped): completed
- Actual answer: The passage does not provide enough information to answer that.
- Verdict (PASS/FAIL/ERROR): PASS
- Reason: it returned a no enough info from chuck

## Case 4: reset URL

Question: **What is the URL of the password reset link?**

Expected: acknowledge that the URL is not provided, or return no match.
Chunk 3 mentions a reset link but supplies no address. Inventing an address
or giving reset advice without acknowledging the missing URL fails this case.

- Retrieval score: 0.4126
- Retrieved source and chunk (or none): sample-policy.txt (chunk 3)
- Generation (completed/skipped): completed
- Actual answer: The passage does not provide enough information to answer that.
- Verdict (PASS/FAIL/ERROR): PASS
- Reason: it returned a no enough info from chuck

## Result

Answer quality score: 4/4

Unsupported details found: 0

Why can retrieval pass while the answer fails: because we expect it not to invent random answers

Clarification: retrieval selects a relevant passage, but the generation step can
still invent details, misread the passage, or omit information needed to answer.
We therefore check retrieval and answer quality separately.

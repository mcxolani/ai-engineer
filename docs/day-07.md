# Day 7: estimate cost

Allow 15–20 minutes. Today you will turn your recorded token counts into a cost
estimate. This exercise runs locally and makes no model API calls.

## 1. Understand the calculation

Your configured model is `gpt-4o-mini`. Its standard text prices, checked on
2026-09-27, are **$0.15 per million input tokens** and **$0.60 per million output
tokens**, in USD. Cached input has a separate rate of $0.075 per million. Source:
[official GPT-4o mini pricing](https://developers.openai.com/api/docs/models/gpt-4o-mini).

For this exercise, assume all input is uncached:

```text
input cost  = input tokens  × input price  / 1,000,000
output cost = output tokens × output price / 1,000,000
total cost  = input cost + output cost
```

Keep the two token counts separate. Multiplying all 306 tokens by one rate would
give the wrong result because input and output have different prices.

## 2. Write a small calculator

Create `estimate_cost.py` beside `evaluate.py`:

```python
input_tokens = 277
output_tokens = 29

# USD per million tokens for gpt-4o-mini, standard pricing, 2026-09-27.
input_price = 0.15
output_price = 0.60

input_cost = input_tokens * input_price / 1_000_000
output_cost = output_tokens * output_price / 1_000_000
cost_per_ticket = input_cost + output_cost

print(f"One ticket: ${cost_per_ticket:.8f}")
print(f"1,000 identical-size tickets: ${cost_per_ticket * 1_000:.5f}")
print(f"10,000 identical-size tickets: ${cost_per_ticket * 10_000:.5f}")
```

Run it from the project root:

```bash
source .venv/bin/activate
python estimate_cost.py
```

Your one-ticket estimate should be **$0.00005895**. Display enough decimal places:
rounding each request to two decimals would display `$0.00` and hide the cost.

The larger estimates assume every ticket uses exactly 277 input and 29 output
tokens. Real tickets vary. This calculation excludes caching discounts, retries,
taxes, and hosting; it is an estimate for the recorded response, not an invoice.
If you change models or use this later, update the rates from the pricing page.

## 3. Try a longer response

Change only `output_tokens` from `29` to `58`, then rerun the calculator.
Explain why the output cost doubles but the entire request cost does not.

Send the original and changed results:

```text
Original one-ticket cost: $__
Original 1,000-ticket estimate: $__
Original 10,000-ticket estimate: $__
One-ticket cost with 58 output tokens: $__
Why the total does not double: __
```

You're done when you can explain the calculation without relying on the script.
You now have a small set of quality, latency, usage, and cost measurements.
Next session: begin saving classifications to PostgreSQL.

Completed: all four calculations were correct: $0.00005895 for one ticket,
$0.05895 for 1,000, $0.58950 for 10,000, and $0.00007635 with 58 output tokens.
The input cost stays fixed while the output cost doubles, so the total does not
double. Doubling both counts at unchanged rates would double the total.

Next: [Day 8 — save a classification](day-08.md).

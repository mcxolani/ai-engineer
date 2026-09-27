input_tokens = 277
output_tokens = 58

# USD per million tokens for gpt-4o-mini, standard pricing, 2026-09-27.
input_price = 0.15
output_price = 0.60

input_cost = input_tokens * input_price / 1_000_000
output_cost = output_tokens * output_price / 1_000_000
cost_per_ticket = input_cost + output_cost

print(f"One ticket: ${cost_per_ticket:.8f}")
print(f"1,000 identical-size tickets: ${cost_per_ticket * 1_000:.5f}")
print(f"10,000 identical-size tickets: ${cost_per_ticket * 10_000:.5f}")

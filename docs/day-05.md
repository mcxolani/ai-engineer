# Day 5: measure response time

Allow 15–20 minutes. Your script now checks the answers. Today you will add a
timer so it also tells you how long each ticket takes.

## 1. Add a timer

Make these small edits to your existing `evaluate.py`. Keep your six test cases.

At the top, add:

```python
from time import perf_counter
```

Below `correct = 0`, add:

```python
durations = []
```

Inside the `for` loop, immediately before its `try:`, add the timer. It must reset
for every ticket. The start of the loop should look like this:

```python
    for number, (message, expected) in enumerate(cases, start=1):
        started = perf_counter()
        try:
            response = client.post("/tickets/classify", json={"message": message})
```

Do not put `started` above the loop: that measures cumulative time since the
script began, rather than the duration of each ticket.

After the existing `except` block, add a `finally` block. The end of the loop
should look like this, with `finally` aligned with `except`:

```python
        except (httpx.HTTPError, ValueError, KeyError) as error:
            print(f"Ticket {number}: ERROR ({error})")
        finally:
            elapsed = perf_counter() - started
            durations.append(elapsed)
            print(f"  Time: {elapsed:.2f}s")
```

`perf_counter()` gives a clock reading suitable for measuring elapsed time.
Subtracting the starting reading gives seconds spent on the attempt. `finally`
runs whether the request succeeds or fails, so failed attempts are timed too.

## 2. Print two useful numbers

At the bottom of the script, after the score print, add:

```python
if durations:
    print(f"Average attempt time: {sum(durations) / len(durations):.2f}s")
    print(f"Slowest attempt: {max(durations):.2f}s")
```

These numbers cover each ticket's HTTP request and local response handling,
including printing the result. They exclude the initial health check. The request
also includes server work, network waiting, and any provider retries; this is not
a measurement of model generation time alone.

## 3. Run your six tickets

Keep the API running, then run this from a second terminal in the project root:

```bash
source .venv/bin/activate
python evaluate.py
```

This makes six classification requests using your paid API connection.
Check that every ticket prints a time and the final score still appears.

Send me:

```text
Score: __ / 6
Average attempt time: __ seconds
Slowest attempt: __ seconds
Errors, if any: __
```

You're done when you can report both quality and timing from one run. There is
no target speed yet; these measurements are your starting point. If an attempt
fails, report it alongside the average so a fast error is not mistaken for a fast
successful answer. Next session: record token usage.

## Progress

Reported run: 6/6, average 3.92 seconds, slowest 6.84 seconds. Review found the
timer started outside the loop, so these timings are not a verified per-ticket
baseline. The timer placement in `evaluate.py` was corrected.

Completed rerun (reported by the learner): **6/6, average 1.31 seconds, slowest
1.91 seconds**. Use this as the initial per-ticket timing baseline. The earlier
cumulative measurements are not comparable to it.

Next: [Day 6 — inspect token usage](day-06.md).

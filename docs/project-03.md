# Support tools — project notes

The read-only lookup from [Day 43](day-43.md) is complete. Connecting it to model
requests starts with [Day 44](day-44.md).

## Goal

Let a support assistant retrieve saved ticket details through a small set of
application functions. Reuse the classifier's database rather than asking the
model to guess a ticket's classification.

## First increment

The [lookup function](../support_tools.py) validates the ticket ID before calling
Project 1's database reader. It returns a structured `found` or `not_found`
result and raises `ToolUnavailable` for missing configuration or database errors.
Its database URL comes from application configuration, separately from tool
arguments. Direct calls make no model requests.

Reported results: 10 tool tests, 60 total tests, passing lint, and a real lookup
of ticket 4 returning `found` with category `technical`. The automated tool tests
use a fake reader; the manual lookup checked the local database.

## Later increments

Day 44 describes the function to a model and inspects a requested tool call.
Following increments will execute the allowed function in application code
and return its result to the model.
Then test invalid arguments, unsupported function names, and bounded execution.

The current ticket service has no user authorization. Any future tool that
changes records will need explicit execution rules and tests for those rules.

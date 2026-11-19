# Support tools — project notes

The read-only lookup, model-request inspection, and execution are complete
through [Day 45](day-45.md). Returning the result to the model is next.

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

Day 44 reported a completed model response requesting `lookup_ticket` for ID 4,
with a call ID and 87 input / 7 output tokens. The request script does not execute
the tool, so this result alone does not establish that the ticket exists.

[Day 45](day-45.md) added the [executor](../execute_ticket_tool.py), which accepts
one known lookup request and prepares its result with the same call ID. Reported
results: 8 executor tests, 68 total tests, passing lint, and ticket 4 found as
technical. Unknown names and invalid JSON skipped the lookup. These steps have
not yet sent the saved ticket result to the model.

[Day 46](day-46.md) will add a second model request containing the question,
function call, and function result. It will disable further tool calls and check
the final answer against the stored classification.

The current ticket service has no user authorization. Any future tool that
changes records will need explicit execution rules and tests for those rules.

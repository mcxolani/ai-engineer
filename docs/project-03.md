# Support tools — project notes

The read-only lookup, model-request inspection, execution, and final response
are complete through [Day 46](day-46.md). An HTTP endpoint is next.

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

[Day 46](day-46.md) added a second model request containing the question,
function call, and result. It disables further tool calls and returned an answer
that agreed with ticket 4's stored technical / medium classification. This full
flow has two model requests and one database read. If lookup fails, it stops
before the second model request.

[Day 47](day-47.md) will expose this flow through the support API with input
validation, response metadata, and safe error mapping.

The current ticket service has no user authorization. Any future tool that
changes records will need explicit execution rules and tests for those rules.

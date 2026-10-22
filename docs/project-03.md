# Support tools — project notes

Project 3 begins with [Day 43](day-43.md). Implementation is pending.

## Goal

Let a support assistant retrieve saved ticket details through a small set of
application functions. Reuse the classifier's database rather than asking the
model to guess a ticket's classification.

## First increment

Build a read-only ticket lookup with validated arguments, a structured result,
and distinct handling for missing tickets and unavailable storage. Test it with
a fake reader, then read an existing ticket from the local Project 1 database.
This first increment makes no model calls.

## Later increments

Describe the function to a model, inspect a requested tool call, execute the
allowed function in application code, and return its result to the model.
Then test invalid arguments, unsupported function names, and bounded execution.

The current ticket service has no user authorization. Any future tool that
changes records will need explicit execution rules and tests for those rules.

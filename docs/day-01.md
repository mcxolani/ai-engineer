# Day 1: send a message, get a result

Spend about 20 minutes on this. Today's goal is to understand one request.

## 1. Run it

Start the server using the [README](../README.md), then open
<http://127.0.0.1:8000/docs> and send:

```json
{"message": "My payment went through twice"}
```

You get four fields:

- `category`: what the ticket is about.
- `priority`: how urgent it is.
- `sentiment`: the customer's expressed tone.
- `summary`: a short description.

The demo always returns the same result. We will connect a real model later.

## 2. Follow the code

Open `app/main.py` and find `classify_ticket`. It receives the message and calls
`classify_message` in `app/classifier.py`. That function returns the result.

`app/schemas.py` defines which fields and values are allowed. Try sending an empty
message: the API rejects it before calling the classifier.

## 3. Make one small change

In `app/classifier.py`, change the demo's summary text. Send the request again
and check that your new text appears.

You're done when you can point to where the message enters and where the result
comes from. Next session: replace the fixed demo answer with a real AI response.

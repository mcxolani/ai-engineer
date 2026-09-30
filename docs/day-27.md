# Day 27: return answers as data

Allow 20–25 minutes. Your answer script currently prints its result inside
`main()`. Today you will give another piece of code a way to request an answer
and receive its fields. This prepares the assistant for an API endpoint.

## 1. Return a dictionary

In `ask_document.py`, keep the imports and `INSTRUCTIONS` unchanged. Replace
everything from `def main():` to the end of the file with:

```python
def answer_question(question):
    question = question.strip()
    chunk, score, embedding_tokens = find_chunk(question)
    result = {
        "answer": "I couldn't find a suitable passage in the document.",
        "source": None,
        "chunk_id": None,
        "retrieval_score": score,
        "generation": "skipped",
        "embedding_input_tokens": embedding_tokens,
        "generation_input_tokens": 0,
        "generation_output_tokens": 0,
    }

    if chunk is None:
        return result

    with OpenAI(timeout=20.0, max_retries=0) as client:
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=INSTRUCTIONS,
            input=json.dumps({"question": question, "passage": chunk["text"]}),
            max_output_tokens=200,
            store=False,
        )

    if response.status != "completed" or not response.output_text.strip():
        raise RuntimeError("The model did not return a complete text answer.")

    usage = response.usage
    result.update(
        answer=response.output_text.strip(),
        source=chunk["source"],
        chunk_id=chunk["id"],
        generation="completed",
        generation_input_tokens=usage.input_tokens if usage is not None else None,
        generation_output_tokens=usage.output_tokens if usage is not None else None,
    )
    return result


def main():
    result = answer_question(input("Question: "))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

`answer_question` returns a Python dictionary. `main` handles the terminal
prompt and displays that dictionary as JSON. Other code can import the function
and read fields such as `result["answer"]` and `result["chunk_id"]`.

The early return handles no match. When generation runs, `result.update(...)`
fills in the answer and metadata. A missing usage report is represented by
`None`. When generation is skipped, both generation token counts are zero.

## 2. Check the import

Run from the project root:

```bash
source .venv/bin/activate
python -c "from ask_document import answer_question; print('Import ready')"
```

Expect `Import ready`, with no question prompt or API request. Calling the
function is what performs retrieval and, if a passage is accepted, generation.

## 3. Check two results

Run `python ask_document.py` for each question below:

| Question | Expected fields |
| --- | --- |
| `On which days and at what times is support available?` | `source` is `sample-policy.txt`, `chunk_id` is 1, `generation` is `completed` |
| `banana` | `source` and `chunk_id` are `null`, `generation` is `skipped`, generation token counts are 0 |

Python's `None` appears as `null` in JSON. Compare the hours answer with the
document as before; correct metadata does not guarantee correct answer text.

These checks normally make three paid requests: two query embeddings and one
generation. Reuse the saved document vectors and the existing 0.30 cutoff.

The `source` field records the passage supplied to the model. The `generation`
field records whether generation ran successfully. A response saying the passage
lacks information still has `generation: completed`; this field is not an answer
quality verdict. API errors still raise exceptions rather than becoming no-match
results.

## Done when

Send:

```text
Import without prompt: yes/no
Hours answer: __
Hours source / chunk / generation: __ / __ / __
banana source / chunk / generation: __ / __ / __
banana generation input / output tokens: __ / __
Why return a dictionary instead of only printing: __
```

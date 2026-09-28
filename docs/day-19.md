# Day 19: create your first embedding

Allow 15–20 minutes. Today you will turn one sentence into a list of numbers.

## 1. Understand the idea

Your keyword search compares whole words: `login` is different from both `sign`
and `in`. An **embedding** represents text as a list of numbers, called a
vector. Comparing these vectors can help find related text even when the wording
differs. See the [official embeddings guide](https://developers.openai.com/api/docs/guides/embeddings).

Today we will inspect one vector. Comparing vectors and searching your document
will come next.

## 2. Create the script

Use the existing `OPENAI_API_KEY` in your project's `.env` file. The packages
are already installed. Create `embed_text.py` in the project root:

```python
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

model = "text-embedding-3-small"
text = "I cannot sign in to my account."

with OpenAI(timeout=20.0, max_retries=0) as client:
    response = client.embeddings.create(
        model=model,
        input=text,
        encoding_format="float",
    )

vector = response.data[0].embedding

print(f"Model: {response.model}")
print(f"Text: {text}")
print(f"Dimensions: {len(vector)}")
print(f"First five numbers: {vector[:5]}")
print(f"Input tokens: {response.usage.prompt_tokens}")
```

This script sends the example sentence to OpenAI and makes one paid embeddings
request per run, with automatic retries disabled. It calls the API even if your
classifier uses demo mode. There is no need to change `CLASSIFIER_PROVIDER` or
`OPENAI_MODEL`, or start the API server or database.

Run it from the project root:

```bash
source .venv/bin/activate
python embed_text.py
```

## 3. Read the result

Expect `Dimensions: 1536`: that is the default vector length for
`text-embedding-3-small`. Embeddings requests are billed by input tokens.
See the [official guide's response example](https://developers.openai.com/api/docs/guides/embeddings#how-to-get-embeddings).

The script prints just the first five numbers to keep the output readable.
It still holds the complete vector in `vector`.

Keep these two counts separate:

- **Dimensions:** the number of values in the returned vector.
- **Input tokens:** the pieces of input text processed by the model.

The 1,536 values do not mean the sentence has 1,536 tokens. You do not need to
interpret each individual number; later we will compare complete vectors.
This exercise does not change the keyword search or its 4/5 baseline.

## Done when

Send:

```text
Model: __
Dimensions: __
First five numbers printed: yes/no
Input tokens: __
What does dimensions mean: __
```

Completed: reported `text-embedding-3-small`, 1,536 dimensions, first five
values printed, and 8 input tokens. Correctly explained dimensions as the
number of values in the vector.

Next: [Day 20 — compare embeddings](day-20.md).

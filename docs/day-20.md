# Day 20: compare embeddings

Allow 15–20 minutes. Yesterday you created one vector. Today you will compare
vectors for `login`, `sign in`, and `banana`.

## 1. Understand the score

**Cosine similarity** compares the direction of two vectors. A higher score
means they point in more similar directions. For text embeddings, we use this
to help rank related text. OpenAI recommends this comparison in its
[embeddings guide](https://developers.openai.com/api/docs/guides/embeddings#which-distance-function-should-i-use).

The mathematical range is -1 to 1. A vector compared with itself scores about 1.
The score is not a probability: 0.7 does not mean a 70% chance of a correct answer.

## 2. Create the comparison script

Create `compare_embeddings.py` in the project root. Use your existing `.env`
and installed packages, as in Day 19.

```python
from math import sqrt
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def cosine_similarity(left, right):
    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_length = sqrt(sum(value * value for value in left))
    right_length = sqrt(sum(value * value for value in right))
    return dot_product / (left_length * right_length)


load_dotenv(Path(__file__).resolve().parent / ".env")

texts = ["login", "sign in", "banana"]

with OpenAI(timeout=20.0, max_retries=0) as client:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        encoding_format="float",
    )

vectors = {item.index: item.embedding for item in response.data}
login = vectors[0]
sign_in = vectors[1]
banana = vectors[2]

print(f"Vectors returned: {len(vectors)}")
print(f"login / login: {cosine_similarity(login, login):.4f}")
print(f"login / sign in: {cosine_similarity(login, sign_in):.4f}")
print(f"login / banana: {cosine_similarity(login, banana):.4f}")
print(f"Input tokens: {response.usage.prompt_tokens}")
```

Passing the list in `input` requests three embeddings in one API request.
Each returned `index` identifies the original input: 0 is `login`, 1 is
`sign in`, and 2 is `banana`.

The function multiplies matching vector positions and adds them, then divides
by the two vector lengths. It expects nonzero vectors of the same size, as
returned here by the same embedding model. It compares all 1,536 values.
You do not need to memorize the formula.

## 3. Run and compare

```bash
source .venv/bin/activate
python compare_embeddings.py
```

Each run makes one paid API request containing the three texts, with retries
disabled. The printed input token count covers all three texts.

Check that:

- Three vectors are returned.
- `login / login` prints approximately `1.0000`.
- `login / sign in` scores higher than `login / banana`.

The last comparison is our expectation for these examples. Report your actual
scores; there is no particular decimal value you need to reproduce. Unrelated
text can still have a positive score.

Next, we will use this comparison to rank the three chunks in your document.
We will also need a way to handle questions that the document cannot answer:
the highest score alone does not prove that a useful match exists.

## Done when

Send:

```text
Vectors returned: __
login / login: __
login / sign in: __
login / banana: __
Which phrase is closer to login: __
Does a score of 0.7 mean 70% confidence: __
```

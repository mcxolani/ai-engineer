# Day 16: load and split a document

Allow 15–20 minutes. Today starts Project 2: a document knowledge assistant.
The first step is preparing text that the assistant can search later.
This exercise runs locally with Python and needs no API call or database.

## 1. Read the sample

Open [sample-policy.txt](../documents/sample-policy.txt). It contains three
paragraphs of fictional support guidance, separated by blank lines.

We will make each paragraph one **chunk**: a smaller piece of the document.
Keeping its source filename will help us identify where an answer came from later.

## 2. Load and split it

Create `chunk_document.py` in the project root, beside `evaluate.py`:

```python
from pathlib import Path


source = Path(__file__).resolve().parent / "documents" / "sample-policy.txt"
text = source.read_text(encoding="utf-8")

paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
chunks = [
    {"id": number, "source": source.name, "text": paragraph}
    for number, paragraph in enumerate(paragraphs, start=1)
]

print(f"Source: {source.name}")
print(f"Chunks: {len(chunks)}")
for chunk in chunks:
    print(f"\nChunk {chunk['id']} ({chunk['source']}):")
    print(chunk["text"])
```

Run it from the project root:

```bash
source .venv/bin/activate
python chunk_document.py
```

Expect `Chunks: 3`. The chunks should start with `Support hours:`,
`Duplicate payments:`, and `Account access:`.

`read_text` loads the file, `split("\n\n")` separates paragraphs, and
`enumerate(..., start=1)` gives each chunk a number. The `if part.strip()`
condition skips empty pieces.

## 3. Check your understanding

Which chunk would help answer **“What should I do if I cannot sign in?”**
Read the output and choose the chunk yourself. Today we are preparing the text;
later the program will search for a relevant chunk.

This simple splitter suits our small sample. Long paragraphs will eventually
need a size limit, and multiple documents will need IDs that include the source.

## Done when

Send:

```text
Source: __
Chunks: __
Chunk for the sign-in question: __
Why keep the source filename: __
```

Completed: reported three chunks from `sample-policy.txt`, correctly selected
chunk 3 for the sign-in question, and explained that the filename identifies
where the answer came from.

Next: [Day 17 — find a chunk with keywords](day-17.md).

import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from search_document import chunks

root = Path(__file__).resolve().parent
load_dotenv(root / ".env")
model = "text-embedding-3-small"

if not chunks:
    raise SystemExit("The document has no chunks to embed.")

with OpenAI(timeout=20.0, max_retries=0) as client:
    response = client.embeddings.create(
        model=model,
        input=[chunk["text"] for chunk in chunks],
        encoding_format="float",
    )

vectors = {item.index: item.embedding for item in response.data}
saved_chunks = [
    {**chunk, "embedding": vectors[index]}
    for index, chunk in enumerate(chunks)
]
saved = {"model": model, "chunks": saved_chunks}

output = root / "data" / "embeddings.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(saved), encoding="utf-8")

print(f"Saved chunks: {len(saved_chunks)}")
print(f"Dimensions per chunk: {len(saved_chunks[0]['embedding'])}")
print(f"File: {output.relative_to(root)}")
print(f"Build input tokens: {response.usage.prompt_tokens}")

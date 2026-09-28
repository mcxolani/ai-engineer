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

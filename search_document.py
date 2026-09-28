import re
from pathlib import Path


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


source = Path(__file__).resolve().parent / "documents" / "sample-policy.txt"
text = source.read_text(encoding="utf-8")
paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
chunks = [
    {"id": number, "source": source.name, "text": paragraph}
    for number, paragraph in enumerate(paragraphs, start=1)
]

query = input("Search keywords: ")
query_words = words(query)
best_chunk = None
best_score = 0

for chunk in chunks:
    score = len(query_words & words(chunk["text"]))
    if score > best_score:
        best_chunk = chunk
        best_score = score

if best_chunk is None:
    print("No matching chunk found.")
else:
    print(f"Source: {best_chunk['source']}")
    print(f"Chunk: {best_chunk['id']}")
    print(f"Matching words: {best_score}")
    print(best_chunk["text"])

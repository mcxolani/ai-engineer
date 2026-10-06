import re
from pathlib import Path


def load_chunks(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError("The document folder does not exist.")

    chunks = []
    for source in sorted(folder.glob("*.txt")):
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        for number, paragraph in enumerate(paragraphs, start=1):
            chunks.append({"id": number, "source": source.name, "text": paragraph})
    return chunks


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent / "documents"
    chunks = load_chunks(folder)
    for chunk in chunks:
        print(f"{chunk['source']} / chunk {chunk['id']}")
    print(f"Total chunks: {len(chunks)}")

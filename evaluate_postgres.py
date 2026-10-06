from pgvector_search import MINIMUM_SCORE, find_chunk

cases = [
    ("password reset", ("sample-policy.txt", 3)),
    ("duplicate payment", ("sample-policy.txt", 2)),
    ("support hours", ("sample-policy.txt", 1)),
    ("banana", None),
    ("login", ("sample-policy.txt", 3)),
    ("How many days per week can employees work remotely?", ("remote-work-policy.txt", 1)),
]

passed = 0
total_tokens = 0
print(f"Minimum score: {MINIMUM_SCORE:.2f}")

for query, expected in cases:
    chunk, similarity, tokens = find_chunk(query)
    actual = (chunk["source"], chunk["id"]) if chunk is not None else None
    total_tokens += tokens
    correct = actual == expected
    if correct:
        passed += 1

    status = "PASS" if correct else "FAIL"
    print(f"{query}: {status} | expected={expected}, actual={actual}")
    print(f"  Similarity: {similarity:.4f} | Input tokens: {tokens}")

print(f"Score: {passed}/{len(cases)}")
print(f"Total query input tokens: {total_tokens}")

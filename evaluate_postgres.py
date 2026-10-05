from pgvector_search import MINIMUM_SCORE, find_chunk

cases = [
    ("password reset", 3),
    ("duplicate payment", 2),
    ("support hours", 1),
    ("banana", None),
    ("login", 3),
]

passed = 0
total_tokens = 0
print(f"Minimum score: {MINIMUM_SCORE:.2f}")

for query, expected_id in cases:
    chunk, similarity, tokens = find_chunk(query)
    actual_id = chunk["id"] if chunk is not None else None
    total_tokens += tokens
    correct = actual_id == expected_id
    if correct:
        passed += 1

    status = "PASS" if correct else "FAIL"
    print(f"{query}: {status} | expected={expected_id}, actual={actual_id}")
    print(f"  Similarity: {similarity:.4f} | Input tokens: {tokens}")

print(f"Score: {passed}/{len(cases)}")
print(f"Total query input tokens: {total_tokens}")

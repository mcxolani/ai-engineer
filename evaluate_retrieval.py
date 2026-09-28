from search_document import find_chunk

cases = [
    ("password reset", 3),
    ("duplicate payment", 2),
    ("support hours", 1),
    ("banana", None),
    ("login", 3),
]

passed = 0
for query, expected_id in cases:
    chunk, _ = find_chunk(query)
    actual_id = chunk["id"] if chunk is not None else None
    correct = actual_id == expected_id
    if correct:
        passed += 1

    status = "PASS" if correct else "FAIL"
    print(f"{query}: {status} | expected={expected_id}, actual={actual_id}")

print(f"Score: {passed}/{len(cases)}")

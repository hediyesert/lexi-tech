import csv
import json
from itertools import permutations
from pathlib import Path

INPUT = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
OUTPUT = Path("reports/splits/domain_document_split_v0.9.csv")

TARGET = {
    "train": 0.90,
    "validation": 0.05,
    "test": 0.05
}

with INPUT.open(encoding="utf-8") as f:
    documents = [
        json.loads(line)
        for line in f
        if line.strip()
    ]

if len(documents) != 12:
    raise ValueError("12 kanun bekleniyordu.")

ids = [doc["document_id"] for doc in documents]

if len(set(ids)) != 12:
    raise ValueError("Tekrarlanan belge kimliği bulundu.")

total_tokens = sum(doc["token_count"] for doc in documents)

if total_tokens <= 0:
    raise ValueError("Token toplamı geçersiz.")

best = None

for validation, test in permutations(documents, 2):
    val_ratio = validation["token_count"] / total_tokens
    test_ratio = test["token_count"] / total_tokens
    train_ratio = 1 - val_ratio - test_ratio

    error = sum([
        (train_ratio - TARGET["train"]) ** 2,
        (val_ratio - TARGET["validation"]) ** 2,
        (test_ratio - TARGET["test"]) ** 2
    ])

    candidate = (
        error,
        validation["document_id"],
        test["document_id"]
    )

    if best is None or candidate < best[0]:
        best = (
            candidate,
            validation["document_id"],
            test["document_id"]
        )

_, validation_id, test_id = best

assignments = []

for doc in documents:
    if doc["document_id"] == validation_id:
        split = "validation"
    elif doc["document_id"] == test_id:
        split = "test"
    else:
        split = "train"

    assignments.append({
        "document_id": doc["document_id"],
        "law_number": doc["law_number"],
        "title": doc["title"],
        "split": split,
        "token_count": doc["token_count"]
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "document_id",
            "law_number",
            "title",
            "split",
            "token_count"
        ]
    )
    writer.writeheader()
    writer.writerows(assignments)

print("LEXITECH TR - DOMAIN SPLIT PLANI")
print("-" * 55)

for split in ["train", "validation", "test"]:
    rows = [r for r in assignments if r["split"] == split]
    tokens = sum(r["token_count"] for r in rows)

    print(f"\n{split.upper()}")
    print("Kanun sayısı:", len(rows))
    print("Token sayısı:", tokens)
    print("Token oranı: %", round(tokens / total_tokens * 100, 2))

    for row in rows:
        print(" ", row["law_number"], "-", row["title"])

print("\nAyrım planı kaydedildi:", OUTPUT)
print("Henüz veri seti dosyaları oluşturulmadı.")

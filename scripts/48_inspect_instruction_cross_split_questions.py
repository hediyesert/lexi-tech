import json
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

ROOT = Path("data/interim/instruction_dedup_v0.9")
SPLITS = ("train", "validation", "test")


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = "".join(
        char if char.isalnum() else " "
        for char in text
    )
    return re.sub(r"\s+", " ", text).strip()


groups = defaultdict(list)

for split in SPLITS:
    path = ROOT / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            question = record["messages"][0]["content"]

            groups[normalize(question)].append({
                "id": record["id"],
                "split": split,
                "law": record["metadata"]["law_indicator"],
                "source_document": record["metadata"]["source_document"],
                "question": question,
                "answer": record["messages"][1]["content"],
            })

leaks = [
    (question, records)
    for question, records in groups.items()
    if len({r["split"] for r in records}) > 1
]

leaks.sort(key=lambda item: item[0])

print("LEXITECH TR - KÜMELER ARASI SORU İNCELEMESİ")
print("=" * 60)
print("Olası sızıntı grubu:", len(leaks))

for index, (question, records) in enumerate(leaks, 1):
    print(f"\n{'=' * 60}")
    print(f"GRUP {index}")
    print("Normalize edilmiş soru:", question)
    print("Kayıt sayısı:", len(records))

    for record in records:
        print("\n  Kayıt ID:", record["id"])
        print("  Küme:", record["split"])
        print("  Kanun:", record["law"])
        print("  Kaynak dosyası:", record["source_document"])
        print("  Soru:", record["question"])
        print("  Cevap özeti:", record["answer"][:300])

print("\nHiçbir dosya değiştirilmedi.")

import json
import re
import unicodedata
from pathlib import Path
from collections import Counter, defaultdict

INPUT = Path("data/interim/instruction_dedup_v0.9")
OUTPUT = Path("data/interim/instruction_leakage_clean_v0.9")

QUARANTINE = Path(
    "data/interim/instruction_cross_split_quarantine_v0.9.jsonl"
)

REPORT = Path(
    "reports/quality/instruction_leakage_fix_v0.9.json"
)

SPLITS = ("train", "validation", "test")
PRIORITY = {name: i for i, name in enumerate(SPLITS)}


def normalize_question(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    text = "".join(
        ch if ch.isalnum() else " "
        for ch in text
    )
    return re.sub(r"\s+", " ", text).strip()


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


print("LEXITECH TR - VERİ SIZINTISI DÜZELTME")
print("=" * 60)

# 1. AŞAMA: Her sorunun kalacağı kümeyi belirle.
question_splits = defaultdict(set)
old_counts = Counter()

for split in SPLITS:
    for record in read_jsonl(INPUT / f"{split}.jsonl"):
        question = record["messages"][0]["content"]
        key = normalize_question(question)

        question_splits[key].add(split)
        old_counts[split] += 1

cross_split_keys = {
    key for key, splits in question_splits.items()
    if len(splits) > 1
}

preferred_split = {
    key: min(splits, key=lambda s: PRIORITY[s])
    for key, splits in question_splits.items()
}

print("Tespit edilen sızıntı grubu:", len(cross_split_keys))

# Beklenmedik sonuçta sessizce işlem yapmayalım.
if len(cross_split_keys) != 5:
    raise ValueError(
        f"5 sızıntı grubu bekleniyordu; "
        f"{len(cross_split_keys)} bulundu."
    )

# 2. AŞAMA: Temiz sürümü ayrı dosyalara yaz.
OUTPUT.mkdir(parents=True, exist_ok=True)
QUARANTINE.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

kept = Counter()
removed = Counter()
removed_examples = []

handles = {
    split: (OUTPUT / f"{split}.jsonl").open(
        "w", encoding="utf-8"
    )
    for split in SPLITS
}

quarantine_file = QUARANTINE.open(
    "w", encoding="utf-8"
)

try:
    for split in SPLITS:
        for record in read_jsonl(INPUT / f"{split}.jsonl"):
            question = record["messages"][0]["content"]
            key = normalize_question(question)

            if preferred_split[key] != split:
                excluded = {
                    "record": record,
                    "excluded_from_split": split,
                    "retained_in_split": preferred_split[key],
                    "reason": "cross_split_normalized_question"
                }

                quarantine_file.write(
                    json.dumps(
                        excluded,
                        ensure_ascii=False
                    ) + "\n"
                )

                removed[split] += 1

                removed_examples.append({
                    "id": record["id"],
                    "question": question,
                    "excluded_from": split,
                    "retained_in": preferred_split[key]
                })

                continue

            handles[split].write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

            kept[split] += 1

finally:
    for handle in handles.values():
        handle.close()
    quarantine_file.close()

# 3. AŞAMA: Yeni dosyaları bağımsız kontrol et.
new_question_splits = defaultdict(set)
source_document_splits = defaultdict(set)
seen_ids = set()
errors = []

for split in SPLITS:
    for record in read_jsonl(OUTPUT / f"{split}.jsonl"):
        question = record["messages"][0]["content"]
        key = normalize_question(question)

        new_question_splits[key].add(split)

        doc = record["metadata"]["source_document"]
        source_document_splits[str(doc)].add(split)

        record_id = str(record["id"])

        if record_id in seen_ids:
            errors.append(f"Tekrarlanan ID: {record_id}")

        seen_ids.add(record_id)

        if record["metadata"]["split"] != split:
            errors.append(f"Yanlış split etiketi: {record_id}")

        if record["metadata"]["training_approved"] is not False:
            errors.append(f"Onay etiketi hatalı: {record_id}")

for key, splits in new_question_splits.items():
    if len(splits) > 1:
        errors.append(f"Kümeler arası soru: {key[:100]}")

for doc, splits in source_document_splits.items():
    if len(splits) > 1:
        errors.append(f"Kümeler arası kaynak: {doc}")

for split in SPLITS:
    if kept[split] + removed[split] != old_counts[split]:
        errors.append(f"Kayıt kaybı: {split}")

report = {
    "status": "PASS" if not errors else "FAIL",
    "old_counts": dict(old_counts),
    "new_counts": dict(kept),
    "quarantined_counts": dict(removed),
    "cross_split_groups_before": len(cross_split_keys),
    "cross_split_groups_after": sum(
        len(splits) > 1
        for splits in new_question_splits.values()
    ),
    "cross_split_source_documents_after": sum(
        len(splits) > 1
        for splits in source_document_splits.values()
    ),
    "removed_examples": removed_examples,
    "errors": errors,
    "training_approved": False
}

REPORT.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("\nYENİ DAĞILIM")
print("-" * 60)

for split in SPLITS:
    print(
        f"{split}: {old_counts[split]:,} → "
        f"{kept[split]:,} "
        f"(ayrılan: {removed[split]})"
    )

print("\nToplam kalan:", sum(kept.values()))
print("İncelemeye ayrılan:", sum(removed.values()))
print(
    "Kalan kümeler arası soru sızıntısı:",
    report["cross_split_groups_after"]
)
print(
    "Kalan kümeler arası kaynak sızıntısı:",
    report["cross_split_source_documents_after"]
)
print("Hata sayısı:", len(errors))
print("Sonuç:", report["status"])
print("Rapor:", REPORT)
print("İnceleme havuzu:", QUARANTINE)
print("Yeni veri klasörü:", OUTPUT)
print("Önceki dosyalar değiştirilmedi.")

if errors:
    for error in errors[:10]:
        print("HATA:", error)
    raise SystemExit(1)

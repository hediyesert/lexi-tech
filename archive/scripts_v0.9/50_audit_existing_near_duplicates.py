import json
from pathlib import Path
from collections import Counter

ROOT = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)

PAIRS = Path(
    "reports/deduplication/near_duplicate_candidates.jsonl"
)

REPORT = Path(
    "reports/quality/instruction_existing_near_duplicates_v0.9.json"
)

SPLITS = ("train", "validation", "test")

records = {}
counts = Counter()

print("LEXITECH TR - MEVCUT YAKIN TEKRAR DENETİMİ")
print("=" * 60)

# Yeni veri setinin ID ve split bilgilerini yükle.
for split in SPLITS:
    path = ROOT / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            record_id = str(record["id"])

            if record_id in records:
                raise ValueError(
                    f"Tekrarlanan kayıt ID: {record_id}"
                )

            records[record_id] = {
                "split": split,
                "law": str(
                    record["metadata"]["law_indicator"]
                ),
                "question": record["messages"][0]["content"],
            }

            counts[f"records_{split}"] += 1

if len(records) != 124510:
    raise ValueError(
        f"124510 kayıt bekleniyordu, {len(records)} bulundu."
    )

cross_split_examples = []
same_split_examples = []

# Eski doğrulanmış MinHash çiftlerini yeni ID'lerle eşleştir.
with PAIRS.open(encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        pair = json.loads(line)

        left_id = str(pair["left"]["id"])
        right_id = str(pair["right"]["id"])

        counts["old_near_duplicate_pairs"] += 1

        left = records.get(left_id)
        right = records.get(right_id)

        if left is None or right is None:
            counts["pairs_not_fully_retained"] += 1
            continue

        counts["pairs_both_retained"] += 1

        item = {
            "left_id": left_id,
            "right_id": right_id,
            "left_split": left["split"],
            "right_split": right["split"],
            "left_law": left["law"],
            "right_law": right["law"],
            "left_question": left["question"][:250],
            "right_question": right["question"][:250],
            "jaccard": pair.get("jaccard"),
        }

        if left["split"] != right["split"]:
            counts["cross_split_pairs"] += 1

            if len(cross_split_examples) < 10:
                cross_split_examples.append(item)

        else:
            counts["within_split_pairs"] += 1
            counts[
                f"within_{left['split']}"
            ] += 1

            if len(same_split_examples) < 5:
                same_split_examples.append(item)

if (
    counts["pairs_both_retained"]
    + counts["pairs_not_fully_retained"]
    != counts["old_near_duplicate_pairs"]
):
    raise ValueError("Çift sayıları uyuşmuyor.")

report = {
    "dataset": "instruction_leakage_clean_v0.9",
    "method": "reuse_previous_verified_minhash_pairs",
    "previous_method": {
        "threshold": 0.85,
        "num_perm": 128,
        "shingle_size": 3,
        "compared_fields": "question_and_answer",
    },
    "counts": dict(counts),
    "cross_split_examples": cross_split_examples,
    "within_split_examples": same_split_examples,
    "limitations": [
        "Yalnızca eski MinHash analizinde bulunan çiftler tarandı.",
        "Yeni veri setinde sıfırdan MinHash taraması yapılmadı.",
        "Soru metnine özgü yakın tekrar kontrolü yapılmadı.",
        "LSH bütün benzer çiftleri bulmayı garanti etmez.",
        "Hukuki doğruluk ve lisans durumu onaylanmadı.",
    ],
}

REPORT.parent.mkdir(parents=True, exist_ok=True)

REPORT.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("Yeni veri setindeki kayıt:", len(records))
print(
    "Eski rapordaki yakın tekrar çifti:",
    counts["old_near_duplicate_pairs"]
)
print(
    "İki kaydı da yeni veri setinde bulunan çift:",
    counts["pairs_both_retained"]
)
print(
    "En az bir kaydı artık bulunmayan çift:",
    counts["pairs_not_fully_retained"]
)
print(
    "Aynı split içindeki yakın tekrar:",
    counts["within_split_pairs"]
)
print(
    "Farklı splitlerdeki yakın tekrar:",
    counts["cross_split_pairs"]
)

print("\nSPLIT İÇİ DAĞILIM")
for split in SPLITS:
    print(
        f"  {split}:",
        counts[f"within_{split}"]
    )

print("\nFARKLI SPLITLERDEKİ İLK 10 ÖRNEK")
print("-" * 60)

for item in cross_split_examples:
    print(
        f"\n{item['left_split']} / "
        f"{item['right_split']}"
    )
    print("Benzerlik:", item["jaccard"])
    print("Soru 1:", item["left_question"])
    print("Soru 2:", item["right_question"])

print("\nRapor:", REPORT)
print("Hiçbir veri kaydı değiştirilmedi.")
print("Bu kontrol yakın tekrarların tamamını garanti etmez.")

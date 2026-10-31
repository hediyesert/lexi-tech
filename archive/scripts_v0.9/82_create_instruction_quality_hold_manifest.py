import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

BASE = Path("data/interim")

QUEUE = BASE / "instruction_quality_decision_queue_14_v0.9.csv"
DATA = BASE / "instruction_leakage_clean_v0.9"

OUTPUT = BASE / "instruction_quality_hold_manifest_v0.9.json"

if OUTPUT.exists():
    raise SystemExit(
        "Manifesto zaten mevcut; üzerine yazılmadı: "
        + str(OUTPUT)
    )

with QUEUE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 14:
    raise ValueError("14 kayıt bekleniyordu.")

ids = [row["record_id"] for row in rows]

if len(set(ids)) != 14:
    raise ValueError("Tekrarlı kayıt kimliği bulundu.")

for row in rows:
    if row["split"] != "train":
        raise ValueError("Bekletilecek kayıt train dışında.")

    if row["recommended_treatment"] != (
        "hold_from_future_training_pending_review"
    ):
        raise ValueError("Beklenmeyen bekletme kararı.")

    if row["final_human_decision"].strip():
        raise ValueError(
            "Nihai insan kararı bulunan kayıt tespit edildi."
        )

    if not row["quality_reasons"].strip():
        raise ValueError("Kalite gerekçesi eksik.")

wanted = set(ids)
found = set()
split_counts = Counter()
held_counts = Counter()

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            rid = record["id"]

            split_counts[split] += 1

            if rid in wanted:
                if rid in found:
                    raise ValueError(
                        "Bekletilecek bir kayıt birden çok kez bulundu."
                    )

                found.add(rid)
                held_counts[split] += 1

if found != wanted:
    raise ValueError(
        f"Bulunamayan bekletme kaydı: {len(wanted - found)}"
    )

expected_counts = {
    "train": 111782,
    "validation": 6397,
    "test": 6331,
}

if dict(split_counts) != expected_counts:
    raise ValueError(
        f"Split sayıları beklenenden farklı: {dict(split_counts)}"
    )

if dict(held_counts) != {"train": 14}:
    raise ValueError(
        f"Bekletme dağılımı beklenenden farklı: {dict(held_counts)}"
    )

source_sha256 = hashlib.sha256(
    QUEUE.read_bytes()
).hexdigest()

manifest = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "purpose": "instruction_quality_hold",
    "status": "assistant_recommendation_pending_human_review",
    "source_review_file": str(QUEUE),
    "source_review_sha256": source_sha256,
    "total_qa": sum(split_counts.values()),
    "original_split_counts": dict(split_counts),
    "held_split_counts": {
        split: held_counts[split]
        for split in ("train", "validation", "test")
    },
    "proposed_remaining_split_counts": {
        split: split_counts[split] - held_counts[split]
        for split in ("train", "validation", "test")
    },
    "hold_records": [
        {
            "record_id": row["record_id"],
            "split": row["split"],
            "quality_reasons": row["quality_reasons"].split("|"),
            "affected_fields": row["affected_fields"].split("|"),
            "decision_status": "pending_human_review",
        }
        for row in sorted(rows, key=lambda x: x["record_id"])
    ],
    "rules": {
        "future_export_should_exclude_held_ids": True,
        "hold_is_final_deletion": False,
        "hold_is_human_approval": False,
        "hold_grants_training_permission": False,
        "rights_review_still_required": True,
    },
    "actual_records_removed": 0,
    "training_approved": False,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

temporary = OUTPUT.with_suffix(".json.tmp")

with temporary.open(encoding="utf-8", mode="w") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
    f.write("\n")

temporary.replace(OUTPUT)

print("LEXITECH TR - KALITE BEKLETME MANIFESTOSU")
print("=" * 60)
print("Toplam mevcut QA:", manifest["total_qa"])
print("Bekletme manifestosundaki QA:", len(manifest["hold_records"]))

print("\nSPLIT BAZINDA")
for split in ("train", "validation", "test"):
    print(
        f"{split}: "
        f"mevcut={split_counts[split]}, "
        f"bekletme={held_counts[split]}, "
        f"olasi_kalan={split_counts[split] - held_counts[split]}"
    )

print("\nKaynak SHA-256:", source_sha256)
print("Manifesto:", OUTPUT)
print("Nihai insan kararı: 0")
print("Eğitim onayı: verilmedi")
print("Fiilen çıkarılan QA: 0")
print("Ana veri setleri değiştirilmedi.")

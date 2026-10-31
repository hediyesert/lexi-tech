import csv
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path("data/interim/instruction_leakage_clean_v0.9")

REPORT = Path(
    "reports/statistics/instruction_task_distribution_v0.9.json"
)

OUTPUT = Path(
    "data/interim/instruction_task_type_review_70_v0.9.csv"
)

RULES = [
    ("comparison", r"\bfark(?:ı|ları)?\b|\bkarşılaştır|\barasındaki fark\b"),
    ("penalty_sanction", r"\bcezası\b|\bhangi cez|\byaptırım|\bhapis cezası\b"),
    ("procedure_deadline", r"\bsüre(?:si|ler|de)?\b|\bkaç gün\b|\bbaşvur|\bitiraz|\bdava aç|\busul\b|\bnasıl yapılır\b"),
    ("legal_conditions", r"\bşart(?:ı|ları)?\b|\bkoşul(?:u|ları)?\b|\bhangi hallerde\b|\bhangi durumlarda\b|\bne zaman\b"),
    ("definition", r"\bnedir\b|\bne demektir\b|\bne anlama gelir\b|\btanımı\b"),
    ("article_explanation", r"\bmadde\b|\bm\.\s*\d+|\bmd\.\s*\d+|\bmaddesi\b"),
]

patterns = [
    (label, re.compile(pattern, re.IGNORECASE))
    for label, pattern in RULES
]

LABELS = [
    "comparison",
    "penalty_sanction",
    "procedure_deadline",
    "legal_conditions",
    "definition",
    "article_explanation",
    "other",
]

randomizer = random.Random(20261028)

samples = {label: [] for label in LABELS}
seen = Counter()
total = 0

for split in ("train", "validation", "test"):
    path = ROOT / f"{split}.jsonl"

    with path.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)
            question = record["messages"][0]["content"]

            matches = [
                label
                for label, pattern in patterns
                if pattern.search(question)
            ]

            label = matches[0] if matches else "other"

            seen[label] += 1
            total += 1

            item = {
                "record_id": record["id"],
                "automatic_label": label,
                "law_indicator": record["metadata"]["law_indicator"],
                "split": split,
                "question": question,
                "answer": record["messages"][1]["content"],
                "label_correct": "",
                "correct_label": "",
                "review_notes": "",
            }

            # Her kategoriden eşit sayıda rastgele örnek.
            bucket = samples[label]

            if len(bucket) < 10:
                bucket.append(item)
            else:
                index = randomizer.randrange(seen[label])
                if index < 10:
                    bucket[index] = item

expected = json.loads(REPORT.read_text(encoding="utf-8"))

if total != expected["total"]:
    raise ValueError("Toplam kayıt sayısı uyuşmuyor.")

for label in LABELS:
    expected_count = expected["distribution"][label]["count"]

    if seen[label] != expected_count:
        raise ValueError(
            f"{label} dağılımı değişmiş: "
            f"{seen[label]} != {expected_count}"
        )

    if len(samples[label]) != 10:
        raise ValueError(
            f"{label} kategorisinde 10 örnek seçilemedi."
        )

if OUTPUT.exists():
    raise SystemExit(
        "İnceleme dosyası zaten mevcut; üzerine yazılmadı: "
        + str(OUTPUT)
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "review_number",
    "record_id",
    "automatic_label",
    "law_indicator",
    "split",
    "question",
    "answer",
    "label_correct",
    "correct_label",
    "review_notes",
]

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    row_number = 0

    for label in LABELS:
        for item in samples[label]:
            row_number += 1
            writer.writerow({
                "review_number": row_number,
                **item
            })

print("LEXITECH TR - GÖREV TÜRÜ MANUEL DENETİM")
print("=" * 60)
print("İncelenen toplam QA:", total)
print("Görev türü sayısı:", len(LABELS))
print("Her türden örnek:", 10)
print("Manuel inceleme örneği:", row_number)
print("Dosya:", OUTPUT)

print("\nHER KATEGORİDEN İLK ÖRNEK")

for label in LABELS:
    item = samples[label][0]
    print(f"\n{label}")
    print("Soru:", item["question"][:250])

print("\nlabel_correct ve correct_label alanları boş.")
print("Henüz manuel doğrulama yapılmadı.")
print("Mevcut veri setleri değiştirilmedi.")

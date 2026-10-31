import ast
import csv
import json
import random
import re
from collections import Counter
from pathlib import Path

SOURCE = Path(
    "scripts/61_improve_instruction_task_classifier_v092.py"
)
DATA = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)
OLD_REVIEW = Path(
    "data/interim/instruction_task_type_review_70_v0.9.csv"
)
OUTPUT = Path(
    "data/interim/instruction_task_independent_review_50_v0.9.csv"
)

LABELS = [
    "comparison",
    "case_law_analysis",
    "case_application",
    "legal_effect",
    "procedure_deadline",
    "legal_conditions",
    "penalty_sanction",
    "definition",
    "article_explanation",
    "other",
]

# Önceki scripti tekrar çalıştırmadan, yalnızca
# sınıflandırma fonksiyonlarını yükle.
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))

functions = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name in ("matches", "classify")
]

if len(functions) != 2:
    raise ValueError("Sınıflandırıcı fonksiyonları bulunamadı.")

namespace = {"re": re}

exec(
    compile(
        ast.Module(body=functions, type_ignores=[]),
        str(SOURCE),
        "exec"
    ),
    namespace
)

classify = namespace["classify"]

def normalize(text):
    return " ".join(text.casefold().split())

with OLD_REVIEW.open(
    encoding="utf-8-sig", newline=""
) as f:
    old_rows = list(csv.DictReader(f))

if len(old_rows) != 70:
    raise ValueError("Önceki 70 kayıt bulunamadı.")

excluded_ids = {
    row["record_id"] for row in old_rows
}

excluded_questions = {
    normalize(row["question"]) for row in old_rows
}

rng = random.Random(20261028)
samples = {label: [] for label in LABELS}
seen = Counter()

total_scanned = 0
excluded_count = 0

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            total_scanned += 1

            question = record["messages"][0]["content"]

            if (
                record["id"] in excluded_ids
                or normalize(question) in excluded_questions
            ):
                excluded_count += 1
                continue

            label = classify(question)

            if label not in samples:
                raise ValueError(
                    f"Bilinmeyen görev etiketi: {label}"
                )

            seen[label] += 1

            item = {
                "record_id": record["id"],
                "split": split,
                "law_indicator": record["metadata"]["law_indicator"],
                "predicted_label": label,
                "question": question,
                "reviewer_label": "",
                "reviewer_notes": "",
                "review_status": "pending",
            }

            bucket = samples[label]

            if len(bucket) < 5:
                bucket.append(item)
            else:
                index = rng.randrange(seen[label])

                if index < 5:
                    bucket[index] = item

if total_scanned != 124510:
    raise ValueError(
        f"124510 kayıt bekleniyordu: {total_scanned}"
    )

for label in LABELS:
    if len(samples[label]) != 5:
        raise ValueError(
            f"{label}: beş örnek seçilemedi."
        )

if OUTPUT.exists():
    raise SystemExit(
        "İnceleme dosyası zaten mevcut. "
        "Üzerine yazılmadı: " + str(OUTPUT)
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "review_number",
    "record_id",
    "split",
    "law_indicator",
    "predicted_label",
    "question",
    "reviewer_label",
    "reviewer_notes",
    "review_status",
]

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    number = 0

    for label in LABELS:
        for item in samples[label]:
            number += 1
            writer.writerow({
                "review_number": number,
                **item
            })

print("LEXITECH TR - BAĞIMSIZ GÖREV TEST HAVUZU")
print("=" * 60)
print("Taranan toplam QA:", total_scanned)
print("Önceki incelemeden hariç tutulan:", excluded_count)
print("Görev türü:", len(LABELS))
print("Her türden seçilen:", 5)
print("Yeni test örneği:", number)

print("\nKATEGORİLER")
for label in LABELS:
    print(
        f"{label:<25} "
        f"Seçilen: {len(samples[label])} "
        f"Havuz: {seen[label]}"
    )

print("\nDOSYA:", OUTPUT)
print("Doğru etiket alanları boş bırakıldı.")
print("Bağımsız değerlendirme henüz yapılmadı.")
print("Ana veri setleri değiştirilmedi.")

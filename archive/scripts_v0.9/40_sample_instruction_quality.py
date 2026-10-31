import csv
import json
import random
from pathlib import Path
from collections import defaultdict

INPUT = Path(
    "data/interim/instruction_citation_review_v0.9.jsonl"
)

OUTPUT = Path(
    "reports/quality/instruction_manual_review_200_v0.9.csv"
)

SEED = 20261027
rng = random.Random(SEED)

by_law = defaultdict(list)
orion = []

with INPUT.open(encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        record = json.loads(line)
        law = str(record["law_indicator"])

        by_law[law].append(record)

        if record["source"] == "OrionCAF/turkish_law_qa_dataset":
            orion.append(record)

selected = []
selected_ids = set()

# Her kanundan 15 rastgele örnek.
for law in sorted(by_law):
    population = by_law[law]

    if len(population) < 15:
        raise ValueError(
            f"{law}: 15 örnekten az kayıt var."
        )

    for record in rng.sample(population, 15):
        selected.append(record)
        selected_ids.add(str(record["id"]))

# OrionCAF kaynağından 20 ek örnek.
orion_remaining = [
    record for record in orion
    if str(record["id"]) not in selected_ids
]

if len(orion_remaining) < 20:
    raise ValueError(
        "OrionCAF için 20 farklı örnek bulunamadı."
    )

selected.extend(
    rng.sample(orion_remaining, 20)
)

rows = []

for index, record in enumerate(selected, 1):
    rows.append({
        "review_number": index,
        "record_id": record["id"],
        "law_indicator": record["law_indicator"],
        "source": record["source"],
        "source_document": (
            record["source_document"] or ""
        ),
        "question": record["question"],
        "answer": record["answer"],
        "has_case_law_indicator": (
            record["has_case_law_indicator"]
        ),
        "legal_accuracy": "",
        "citation_accuracy": "",
        "question_answer_consistency": "",
        "source_traceability": "",
        "overall_decision": "",
        "review_notes": "",
        "reviewer": "",
        "review_date": ""
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

print("LEXITECH TR - MANUEL KALİTE ÖRNEKLEMİ")
print("=" * 60)
print("Rastgele seçim tohumu:", SEED)
print("İncelenen hukuk alanı:", len(by_law))
print("Her kanundan seçilen:", 15)
print("Ek OrionCAF örneği:", 20)
print("Toplam manuel inceleme kaydı:", len(rows))
print("CSV dosyası:", OUTPUT)

print("\nİLK 5 İNCELEME KAYDI")
print("-" * 60)

for row in rows[:5]:
    print(
        f"\n[{row['review_number']}] "
        f"Kanun: {row['law_indicator']}"
    )
    print("Kaynak:", row["source"])
    print("Soru:", row["question"][:250])
    print("Cevap:", row["answer"][:350])

print("\nManuel değerlendirme alanları boş bırakıldı.")
print("Hiçbir kayıt hukuken onaylanmadı.")
print("Orijinal veri setleri değiştirilmedi.")

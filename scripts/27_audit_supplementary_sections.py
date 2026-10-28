import csv
import json
import re
from pathlib import Path

INPUT = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
OUTPUT = Path(
    "reports/quality/domain_supplementary_boundaries_v0.9.csv"
)

with INPUT.open(encoding="utf-8") as f:
    documents = [
        json.loads(line)
        for line in f
        if line.strip()
    ]

markers = [
    ("unincorporated", re.compile(
        r"İŞLENEMEYEN", re.IGNORECASE
    )),
    ("amendment_table", re.compile(
        r"EK VE DEĞİŞİKLİK GETİREN MEVZUATIN",
        re.IGNORECASE
    )),
    ("effective_date_table", re.compile(
        r"YÜRÜRLÜĞE GİRİŞ", re.IGNORECASE
    )),
]

results = []

print("LEXITECH TR - EK BÖLÜM SINIRI DENETİMİ")
print("=" * 60)

for doc in documents:
    lines = doc["text"].splitlines()

    print(f"\n{doc['law_number']} - {doc['title']}")

    found = []

    for index, line in enumerate(lines):
        for kind, pattern in markers:
            if pattern.search(line):
                found.append((index, kind))

    print("Başlık adayı:", len(found))

    for index, kind in found[:8]:
        context = " ".join(
            line.strip()
            for line in lines[index:index + 3]
        )

        print(
            f"  Satır {index + 1} [{kind}]:",
            context[:170]
        )

        results.append({
            "law_number": doc["law_number"],
            "section_type": kind,
            "line_number": index + 1,
            "heading_context": context[:300],
            "verified": False
        })

    if len(found) > 8:
        print(
            "  Diğer aday sayısı:",
            len(found) - 8
        )

    # Kayda alınan bütün adaylar ilk sekizle sınırlı
    # olmamalı; kalanları da rapora ekle.
    for index, kind in found[8:]:
        context = " ".join(
            line.strip()
            for line in lines[index:index + 3]
        )

        results.append({
            "law_number": doc["law_number"],
            "section_type": kind,
            "line_number": index + 1,
            "heading_context": context[:300],
            "verified": False
        })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "law_number",
            "section_type",
            "line_number",
            "heading_context",
            "verified"
        ]
    )
    writer.writeheader()
    writer.writerows(results)

print("\nGENEL SONUÇ")
print("-" * 60)
print("İncelenen kanun:", len(documents))
print("Başlık adayı:", len(results))
print("Rapor:", OUTPUT)
print("Bütün adaylar manuel doğrulama bekliyor.")
print("Orijinal veri seti değiştirilmedi.")

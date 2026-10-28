import csv
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

CORPUS = Path(
    "data/final/domain_corpus_v0.9_tokenized.jsonl"
)

PLAN = Path(
    "reports/quality/domain_section_plan_v0.9.csv"
)

INPUT = Path(
    "data/interim/instruction_citation_review_v0.9.jsonl"
)

OUTPUT = Path(
    "data/interim/instruction_article_audit_v0.9.jsonl"
)

REPORT = Path(
    "reports/quality/instruction_article_audit_v0.9.json"
)

# Madde atıflarının yaygın yazım biçimleri.
REFERENCE_PATTERNS = [
    re.compile(
        r"(?i)\b(?:madde|md\.?|m\.)\s*(\d{1,4})"
    ),
    re.compile(
        r"(?i)\b(\d{1,4})\s*"
        r"(?:inci|ıncı|uncu|üncü|nci|ncı|ncu|ncü)"
        r"\s+madde"
    ),
    re.compile(
        r"(?i)\b(\d{1,4})\.\s*madde"
    ),
    re.compile(
        r"(?i)\b(\d{1,4})\s+"
        r"maddesi(?:nin|nde|ne|ni)?\b"
    ),
]

HEADING = re.compile(
    r"(?im)^[ \t]*"
    r"(?:(?:mükerrer|ek|geçici)[ \t]+)?"
    r"madde[ \t]+(\d+)"
    r"(?=[ \t.\-–—]|$)"
)

RANGE = re.compile(
    r"(?im)^[ \t]*madde[ \t]+"
    r"(\d+)[ \t]*[–—-][ \t]*(\d+)"
    r"(?=[ \t]*[–—-])"
)


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


with PLAN.open(
    encoding="utf-8",
    newline=""
) as f:
    section_plan = list(csv.DictReader(f))

main_ends = {}

for row in section_plan:
    if row["section_type"] == "main_law":
        main_ends[str(row["law_number"])] = int(
            row["end_char"]
        )

article_index = {}

for doc in read_jsonl(CORPUS):
    law = str(doc["law_number"])

    # Sonraki değişiklik tablolarını ana kanun
    # maddesi gibi değerlendirmemek için.
    main_text = doc["text"][:main_ends[law]]

    numbers = {
        int(match.group(1))
        for match in HEADING.finditer(main_text)
    }

    # Madde 53–55 gibi toplu mülga madde kayıtları.
    for match in RANGE.finditer(main_text):
        first = int(match.group(1))
        last = int(match.group(2))

        if first <= last and last - first <= 100:
            numbers.update(range(first, last + 1))

    article_index[law] = numbers

counts = Counter()
by_law = defaultdict(Counter)
examples = defaultdict(list)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8") as out:
    for record in read_jsonl(INPUT):
        counts["total"] += 1

        law = str(record["law_indicator"])
        answer = record["answer"]

        references = set()

        for pattern in REFERENCE_PATTERNS:
            for match in pattern.finditer(answer):
                references.add(int(match.group(1)))

        found = sorted(
            number
            for number in references
            if number in article_index[law]
        )

        not_found = sorted(
            number
            for number in references
            if number not in article_index[law]
        )

        if not references:
            status = "reference_not_extracted"
        elif not not_found:
            status = "numbers_present_in_target_law"
        else:
            status = "requires_reference_review"

        counts[status] += 1
        by_law[law][status] += 1

        audited = {
            "id": record["id"],
            "law_indicator": law,
            "source": record["source"],
            "source_document": record["source_document"],
            "referenced_article_numbers": sorted(references),
            "numbers_present_in_target_law": found,
            "numbers_not_found_in_target_law": not_found,
            "structural_status": status,
            "legal_accuracy_verified": False,
            "citation_accuracy_verified": False
        }

        out.write(
            json.dumps(audited, ensure_ascii=False)
            + "\n"
        )

        if (
            status != "numbers_present_in_target_law"
            and len(examples[status]) < 5
        ):
            examples[status].append({
                "law": law,
                "question": record["question"][:180],
                "answer": answer[:240],
                "extracted_numbers": sorted(references),
                "numbers_not_found": not_found
            })

report = {
    "total": counts["total"],
    "status_counts": dict(counts),
    "by_law": {
        law: dict(values)
        for law, values in by_law.items()
    },
    "article_index_sizes": {
        law: len(numbers)
        for law, numbers in article_index.items()
    },
    "examples": dict(examples),
    "limitations": [
        "Atiflar sadece cevap metninden sezgisel olarak cikarildi.",
        "Madde numaralari baska bir kanuna ait olabilir.",
        "Mükerrer, ek ve geçici madde türleri tam ayrıştırılmadı.",
        "PDF/OCR hatalari eslesmeleri etkileyebilir.",
        "Madde varligi hukuki dogruluk kaniti degildir."
    ]
}

REPORT.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("LEXITECH TR - MADDE ATFI YAPI DENETİMİ")
print("=" * 60)

print("İncelenen aday:", counts["total"])

print(
    "Madde numarası çıkarılamayan:",
    counts["reference_not_extracted"]
)

print(
    "Numaraları hedef kanunda bulunan:",
    counts["numbers_present_in_target_law"]
)

print(
    "Atıf incelemesi gereken:",
    counts["requires_reference_review"]
)

print("\nKANUN BAZINDA ÖZET")

for law in sorted(article_index):
    c = by_law[law]

    print(
        f"{law}: "
        f"bulunan={c['numbers_present_in_target_law']}, "
        f"inceleme={c['requires_reference_review']}, "
        f"çıkarılamayan={c['reference_not_extracted']}"
    )

print("\nİNCELEME GEREKTİREN İLK 5 ÖRNEK")

for item in examples["requires_reference_review"]:
    print("\nKanun:", item["law"])
    print("Soru:", item["question"])
    print("Çıkarılan numaralar:", item["extracted_numbers"])
    print("Hedef kanunda bulunmayan:", item["numbers_not_found"])

print("\nKayıt dosyası:", OUTPUT)
print("Rapor:", REPORT)
print("Hiçbir kayıt hukuken onaylanmadı.")
print("Mevcut veri setleri değiştirilmedi.")

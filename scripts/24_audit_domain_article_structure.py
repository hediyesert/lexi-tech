import csv
import json
import re
from pathlib import Path

INPUT = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
OUTPUT = Path(
    "reports/quality/domain_article_structure_v0.9.csv"
)

pattern = re.compile(
    r"(?im)^[ \t]*madde[ \t]+(\d+)(?=[ \t.\-–—]|$)"
)

with INPUT.open(encoding="utf-8") as f:
    documents = [
        json.loads(line)
        for line in f
        if line.strip()
    ]

results = []

print("LEXITECH TR - KANUN MADDE YAPISI ANALİZİ")
print("-" * 60)

for doc in documents:
    numbers = [
        int(n)
        for n in pattern.findall(doc["text"])
    ]

    # Baştan itibaren 1, 2, 3... biçimindeki
    # kesintisiz ana madde dizisini incele.
    expected = 1
    for number in numbers:
        if number != expected:
            break
        expected += 1

    consecutive_count = expected - 1
    extra = numbers[consecutive_count:]

    result = {
        "law_number": doc["law_number"],
        "title": doc["title"],
        "detected_headings": len(numbers),
        "initial_consecutive_articles": consecutive_count,
        "additional_matches": len(extra),
        "first_numbers": str(numbers[:5]),
        "last_numbers": str(numbers[-10:]),
        "requires_manual_review": bool(extra) or not numbers
    }

    results.append(result)

    print(f"\n{doc['law_number']} - {doc['title']}")
    print("Tespit edilen başlık:", len(numbers))
    print("Baştan sıralı ana madde:", consecutive_count)
    print("Ek/şüpheli eşleşme:", len(extra))
    print("İlk 5 numara:", numbers[:5])
    print("Son 10 numara:", numbers[-10:])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

print("\nGENEL SONUÇ")
print("-" * 60)
print("İncelenen kanun:", len(results))
print(
    "Ayrıntılı inceleme gerektiren:",
    sum(r["requires_manual_review"] for r in results)
)
print("Rapor:", OUTPUT)
print("Orijinal corpus ve split dosyaları değiştirilmedi.")

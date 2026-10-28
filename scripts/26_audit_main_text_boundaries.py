import json
import re
from pathlib import Path

INPUT = Path(
    "data/final/domain_corpus_v0.9_tokenized.jsonl"
)

PATTERN = re.compile(
    r"(?i)^[ \t]*madde[ \t]+(\d+)(?=[ \t.\-–—]|$)"
)


def print_context(lines, index):
    start = max(0, index - 4)
    end = min(len(lines), index + 5)

    for j in range(start, end):
        print(f"  {j + 1}: {lines[j][:150]}")


with INPUT.open(encoding="utf-8") as f:
    documents = [
        json.loads(line)
        for line in f
        if line.strip()
    ]

print("LEXITECH TR - ANA METİN SINIRI DENETİMİ")
print("=" * 60)

for doc in documents:
    lines = doc["text"].splitlines()
    matches = []

    for i, line in enumerate(lines):
        match = PATTERN.match(line)

        if match:
            matches.append(
                (i, int(match.group(1)))
            )

    decreases = []

    for previous, current in zip(
        matches,
        matches[1:]
    ):
        if current[1] < previous[1]:
            decreases.append(
                (previous, current)
            )

    print(
        f"\n{doc['law_number']} - {doc['title']}"
    )
    print("Normal başlık adayı:", len(matches))
    print("Numara gerilemesi:", len(decreases))

    if not decreases:
        print("Gerileme tespit edilmedi.")
        continue

    previous, current = decreases[0]

    print(
        f"İlk gerileme: "
        f"Madde {previous[1]} → Madde {current[1]}"
    )

    print("\nGERİLEMEDEN ÖNCEKİ BAĞLAM")
    print_context(lines, previous[0])

    print("\nGERİLEMEDEN SONRAKİ BAĞLAM")
    print_context(lines, current[0])

print("\nHiçbir dosya değiştirilmedi.")

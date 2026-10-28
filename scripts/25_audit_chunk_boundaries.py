import json
import re
from pathlib import Path

INPUT = Path(
    "data/final/domain_corpus_v0.9_tokenized.jsonl"
)

MAIN = re.compile(
    r"(?i)^[ \t]*madde[ \t]+(\d+)(?=[ \t.\-–—]|$)"
)

SPECIAL = re.compile(
    r"(?i)^[ \t]*(mükerrer|ek|geçici)"
    r"[ \t]+madde[ \t]+(\d+)"
    r"(?=[ \t.\-–—]|$)"
)

with INPUT.open(encoding="utf-8") as f:
    documents = [
        json.loads(line)
        for line in f
        if line.strip()
    ]

print("LEXITECH TR - CHUNK SINIRI ÖN DENETİMİ")
print("=" * 60)

for doc in documents:
    lines = doc["text"].splitlines()

    main = []
    special = []

    for i, line in enumerate(lines):
        m = MAIN.match(line)
        s = SPECIAL.match(line)

        if m:
            main.append((i, m.group(1)))

        if s:
            special.append((i, s.group(1), s.group(2)))

    last_main_line = main[-1][0] if main else -1

    before = [
        x for x in special
        if x[0] <= last_main_line
    ]

    after = [
        x for x in special
        if x[0] > last_main_line
    ]

    print(f"\n{doc['law_number']} - {doc['title']}")
    print("Normal başlık adayı:", len(main))
    print("Özel başlık adayı:", len(special))
    print("Son normal başlığa kadar özel:", len(before))
    print("Son normal başlıktan sonra özel:", len(after))

    if main:
        i, n = main[-1]
        print(
            "Son normal başlık:",
            f"satır {i + 1}, Madde {n}"
        )

    # Son bölümlerdeki olası tablo eşleşmelerini
    # örneklemek için ilk ve son adayları göster.
    samples = []

    if after:
        samples.extend(after[:2])
        samples.extend(after[-2:])

    seen = set()

    for i, kind, number in samples:
        if i in seen:
            continue
        seen.add(i)

        print(
            f"  ÖRNEK satır {i + 1}:",
            lines[i].strip()[:110]
        )

print("\nBu denetim hiçbir dosyayı değiştirmedi.")

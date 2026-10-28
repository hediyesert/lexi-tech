import json
import re
from pathlib import Path
from collections import Counter, defaultdict

INPUT = Path("data/deduplicated/exact_unique.jsonl")
OUTPUT = Path(
    "reports/quality/instruction_law_mapping_v0.9.json"
)

LAWS = {
    "2709": r"Türkiye Cumhuriyeti Anayasası|\bAnayasa(?:nın|ya|da)?\b",
    "4721": r"Türk Meden[îi] Kanunu",
    "6098": r"Türk Borçlar Kanunu",
    "5237": r"Türk Ceza Kanunu",
    "5271": r"Ceza Muhakemesi Kanunu",
    "4857": r"İş Kanunu",
    "6102": r"Türk Ticaret Kanunu",
    "6502": r"Tüketicinin Korunması Hakkında Kanun",
    "2577": r"İdari Yargılama Usulü Kanunu",
    "213": r"Vergi Usul Kanunu",
    "2004": r"İcra ve İflas Kanunu",
    "5510": r"Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu",
}

PATTERNS = {
    number: re.compile(
        rf"(?:\b{number}\s+sayılı\b|{name})",
        re.IGNORECASE
    )
    for number, name in LAWS.items()
}

stats = defaultdict(Counter)
samples = defaultdict(list)

SELECTED = {
    "0.json",
    "6.json",
    "24.json",
    "253.json",
    "277.json",
    "285.json",
}

with INPUT.open(encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        record = json.loads(line)

        if record.get("source") != "sinanelms/hukukisorular":
            continue

        document = str(
            record.get("source_document") or "unknown"
        )

        question = str(record.get("question") or "")
        answer = str(record.get("answer") or "")

        text = question + "\n" + answer

        matched = [
            number
            for number, pattern in PATTERNS.items()
            if pattern.search(text)
        ]

        stats[document]["total"] += 1

        if not matched:
            stats[document]["no_law_indicator"] += 1
        elif len(matched) == 1:
            stats[document]["single_law_indicator"] += 1
        else:
            stats[document]["multiple_law_indicators"] += 1

        for number in matched:
            stats[document][f"law_{number}"] += 1

        if document in SELECTED and len(samples[document]) < 3:
            samples[document].append({
                "question": question[:220],
                "answer": answer[:300],
                "law_indicators": matched
            })

report = {
    "method": "heuristic_law_mentions_not_verified_sources",
    "documents": {
        name: dict(counts)
        for name, counts in stats.items()
    },
    "samples": dict(samples)
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("LEXITECH TR - KAYNAK DOSYASI / KANUN İLİŞKİSİ")
print("=" * 60)
print("İncelenen kaynak dosyası:", len(stats))

for name in sorted(SELECTED):
    c = stats[name]

    print(f"\nDOSYA: {name}")
    print("Toplam soru-cevap:", c["total"])
    print(
        "Hiç kanun göstergesi bulunmayan:",
        c["no_law_indicator"]
    )
    print(
        "Tek kanun göstergesi bulunan:",
        c["single_law_indicator"]
    )
    print(
        "Birden fazla kanun göstergesi bulunan:",
        c["multiple_law_indicators"]
    )

    found = [
        (number, c[f"law_{number}"])
        for number in LAWS
        if c[f"law_{number}"] > 0
    ]

    print(
        "En sık kanun göstergeleri:",
        sorted(found, key=lambda x: -x[1])[:5]
    )

    for i, item in enumerate(samples[name], 1):
        print(f"\n  ÖRNEK {i}")
        print("  Soru:", item["question"])
        print("  Cevap:", item["answer"])
        print(
            "  Kanun göstergeleri:",
            item["law_indicators"]
        )

print("\nRapor:", OUTPUT)
print("Bu işlem kaynak doğrulaması değildir.")
print("Hiçbir veri kaydı değiştirilmedi.")

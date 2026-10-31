import json
import re
from pathlib import Path
from collections import Counter, defaultdict

INPUT = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)

OUTPUT = Path(
    "reports/statistics/instruction_task_distribution_v0.9.json"
)

PATTERNS = [
    (
        "comparison",
        r"\bfark(?:ı|ları)?\b|"
        r"\bkarşılaştır|"
        r"\barasındaki fark\b"
    ),
    (
        "penalty_sanction",
        r"\bcezası\b|"
        r"\bhangi cez|"
        r"\byaptırım|"
        r"\bhapis cezası\b"
    ),
    (
        "procedure_deadline",
        r"\bsüre(?:si|ler|de)?\b|"
        r"\bkaç gün\b|"
        r"\bbaşvur|"
        r"\bitiraz|"
        r"\bdava aç|"
        r"\busul\b|"
        r"\bnasıl yapılır\b"
    ),
    (
        "legal_conditions",
        r"\bşart(?:ı|ları)?\b|"
        r"\bkoşul(?:u|ları)?\b|"
        r"\bhangi hallerde\b|"
        r"\bhangi durumlarda\b|"
        r"\bne zaman\b"
    ),
    (
        "definition",
        r"\bnedir\b|"
        r"\bne demektir\b|"
        r"\bne anlama gelir\b|"
        r"\btanımı\b"
    ),
    (
        "article_explanation",
        r"\bmadde\b|"
        r"\bm\.\s*\d+|"
        r"\bmd\.\s*\d+|"
        r"\bmaddesi\b"
    ),
]

compiled = [
    (label, re.compile(pattern, re.IGNORECASE))
    for label, pattern in PATTERNS
]

counts = Counter()
by_split = defaultdict(Counter)
by_law = defaultdict(Counter)
examples = defaultdict(list)

for split in ("train", "validation", "test"):
    path = INPUT / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            question = record["messages"][0]["content"]
            law = str(record["metadata"]["law_indicator"])

            matches = [
                label for label, pattern in compiled
                if pattern.search(question)
            ]

            # Her soru için birincil görev türü.
            primary = matches[0] if matches else "other"

            counts[primary] += 1
            by_split[split][primary] += 1
            by_law[law][primary] += 1

            if len(examples[primary]) < 5:
                examples[primary].append({
                    "id": record["id"],
                    "question": question,
                    "law": law,
                    "split": split,
                    "all_matched_types": matches
                })

total = sum(counts.values())

if total != 124510:
    raise ValueError(
        f"124510 kayıt bekleniyordu, {total} bulundu."
    )

report = {
    "version": "v0.9",
    "method": "question_keyword_heuristics",
    "status": "automatic_labels_not_human_verified",
    "total": total,
    "distribution": {
        label: {
            "count": count,
            "percent": round(count * 100 / total, 2)
        }
        for label, count in counts.most_common()
    },
    "by_split": {
        split: dict(values)
        for split, values in by_split.items()
    },
    "by_law": {
        law: dict(values)
        for law, values in by_law.items()
    },
    "examples": dict(examples),
    "limitations": [
        "Etiketler yalnızca soru metnindeki anahtar sözcüklerle atanır.",
        "Bir soru birden fazla görev türünü kapsayabilir.",
        "Birincil etiket ilk eşleşen kategoriye göre seçilir.",
        "Other kategorisi görev türünün bilinmediği anlamına gelir.",
        "Etiket doğruluğu manuel örneklemle henüz ölçülmedi."
    ]
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("LEXITECH TR - INSTRUCTION GÖREV ANALİZİ")
print("=" * 55)
print("Toplam kayıt:", total)

print("\nGÖREV TÜRÜ DAĞILIMI")
for label, count in counts.most_common():
    percent = count * 100 / total
    print(f"{label:<25} {count:>7,}  %{percent:.2f}")

print("\nHER TÜRDEN İLK 2 ÖRNEK")
for label, items in examples.items():
    print(f"\n{label}:")
    for item in items[:2]:
        print(" -", item["question"][:180])

print("\nRapor:", OUTPUT)
print("Etiketler henüz manuel doğrulanmadı.")
print("Veri setleri değiştirilmedi.")

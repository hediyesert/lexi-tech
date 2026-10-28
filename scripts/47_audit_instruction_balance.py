import json
import re
import unicodedata
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path("data/interim/instruction_dedup_v0.9")

REPORT = Path(
    "reports/quality/instruction_balance_audit_v0.9.json"
)

SPLITS = ("train", "validation", "test")


def normalize_question(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()

    # Noktalama ve boşluk farklılıklarını görmezden gel.
    text = "".join(
        char if char.isalnum() else " "
        for char in text
    )

    return re.sub(r"\s+", " ", text).strip()


law_counts = defaultdict(Counter)
split_counts = Counter()
question_splits = defaultdict(set)
document_splits = defaultdict(set)

for split in SPLITS:
    path = ROOT / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)

            law = str(
                record["metadata"]["law_indicator"]
            )

            question = record["messages"][0]["content"]

            document = str(
                record["metadata"]["source_document"]
            )

            law_counts[law][split] += 1
            split_counts[split] += 1

            question_splits[
                normalize_question(question)
            ].add(split)

            document_splits[document].add(split)


question_leaks = [
    question
    for question, splits in question_splits.items()
    if len(splits) > 1
]

document_leaks = [
    document
    for document, splits in document_splits.items()
    if len(splits) > 1
]

weak_laws = []

print("LEXITECH TR - INSTRUCTION DENGE DENETİMİ")
print("=" * 65)

print("\nKANUN BAZINDA DAĞILIM")
print(
    f"{'Kanun':<10}"
    f"{'Train':>12}"
    f"{'Validation':>14}"
    f"{'Test':>10}"
    f"{'Toplam':>12}"
)

for law in sorted(law_counts):
    counts = law_counts[law]
    total = sum(counts.values())

    print(
        f"{law:<10}"
        f"{counts['train']:>12,}"
        f"{counts['validation']:>14,}"
        f"{counts['test']:>10,}"
        f"{total:>12,}"
    )

    if counts["validation"] < 30 or counts["test"] < 30:
        weak_laws.append({
            "law_number": law,
            "validation": counts["validation"],
            "test": counts["test"]
        })


print("\nGENEL SONUÇ")
print("-" * 65)

print("Toplam kayıt:", sum(split_counts.values()))
print("Train:", split_counts["train"])
print("Validation:", split_counts["validation"])
print("Test:", split_counts["test"])
print("Kaynak dosyası sayısı:", len(document_splits))

print(
    "Farklı kümelere düşen kaynak dosyası:",
    len(document_leaks)
)

print(
    "Noktalama farkı giderildiğinde "
    "kümeler arası aynı soru:",
    len(question_leaks)
)

print(
    "Validation veya testte 30'dan az "
    "örneği olan kanun:",
    len(weak_laws)
)

for item in weak_laws:
    print(
        f"  {item['law_number']}: "
        f"validation={item['validation']}, "
        f"test={item['test']}"
    )


report = {
    "version": "v0.9",
    "status": "audit_only",
    "split_counts": dict(split_counts),
    "law_distribution": {
        law: dict(counts)
        for law, counts in law_counts.items()
    },
    "source_document_count": len(document_splits),
    "cross_split_document_count": len(document_leaks),
    "cross_split_punctuation_normalized_questions": len(
        question_leaks
    ),
    "cross_split_question_examples": question_leaks[:5],
    "weakly_represented_laws": weak_laws,
    "limitations": [
        "Bu kontrol anlamsal yakın tekrarları tespit etmez.",
        "Düşük örnek sayısı tek başına veri hatası değildir.",
        "Kaynak doğruluğu ve lisans durumu onaylanmadı.",
        "Hukuki doğruluk değerlendirmesi tamamlanmadı."
    ]
}

REPORT.parent.mkdir(parents=True, exist_ok=True)

REPORT.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("\nRapor:", REPORT)
print("Hiçbir veri seti değiştirilmedi.")

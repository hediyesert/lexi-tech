import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path("data/final/instruction_v0.9")

OUTPUT = Path(
    "data/interim/instruction_dedup_v0.9"
)

QUARANTINE = Path(
    "data/interim/instruction_alternative_answers_v0.9.jsonl"
)

REPORT = Path(
    "reports/quality/instruction_dedup_report_v0.9.json"
)

SPLITS = ("train", "validation", "test")


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return re.sub(
        r"\s+", " ", text
    ).strip().casefold()


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


# 1. GEÇİŞ: Aynı soruya verilen farklı cevapları belirle.
groups = {}
original_counts = Counter()

for split in SPLITS:
    for record in read_jsonl(ROOT / f"{split}.jsonl"):
        question = normalize(
            record["messages"][0]["content"]
        )

        answer = normalize(
            record["messages"][1]["content"]
        )

        if question not in groups:
            groups[question] = {
                "answers": set(),
                "splits": set(),
                "count": 0
            }

        group = groups[question]
        group["answers"].add(answer)
        group["splits"].add(split)
        group["count"] += 1

        original_counts[split] += 1


# Aynı sorunun farklı splitlerde olmaması gerekir.
leaked = [
    question
    for question, group in groups.items()
    if len(group["splits"]) > 1
]

if leaked:
    raise ValueError(
        f"Kümeler arası aynı soru bulundu: {len(leaked)}"
    )


# 2. GEÇİŞ: Güvenli adayları ve inceleme kayıtlarını ayır.
OUTPUT.mkdir(parents=True, exist_ok=True)
QUARANTINE.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

seen = set()
counts = Counter()
kept_by_split = Counter()

handles = {
    split: (OUTPUT / f"{split}.jsonl").open(
        "w", encoding="utf-8"
    )
    for split in SPLITS
}

quarantine_handle = QUARANTINE.open(
    "w", encoding="utf-8"
)

try:
    for split in SPLITS:
        for record in read_jsonl(
            ROOT / f"{split}.jsonl"
        ):
            question = normalize(
                record["messages"][0]["content"]
            )

            group = groups[question]

            if len(group["answers"]) > 1:
                # Farklı cevapları bulunan soruların
                # bütün versiyonlarını sakla.
                review_record = {
                    **record,
                    "review_reason": "multiple_answer_versions",
                    "answer_version_count": len(
                        group["answers"]
                    ),
                    "review_status": "pending"
                }

                quarantine_handle.write(
                    json.dumps(
                        review_record,
                        ensure_ascii=False
                    ) + "\n"
                )

                counts["alternative_answer_records"] += 1
                continue

            if question in seen:
                # Aynı sorunun aynı cevabını ikinci
                # kez yazma.
                counts["identical_answer_duplicates_skipped"] += 1
                continue

            seen.add(question)

            # Mevcut eğitim onayı alanı False kalıyor.
            record["metadata"]["training_approved"] = False
            record["metadata"]["quality_status"] = (
                "deduplicated_pending_legal_review"
            )

            handles[split].write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

            kept_by_split[split] += 1
            counts["kept"] += 1

finally:
    for handle in handles.values():
        handle.close()

    quarantine_handle.close()


alternative_groups = sum(
    len(group["answers"]) > 1
    for group in groups.values()
)

identical_groups = sum(
    group["count"] > 1
    and len(group["answers"]) == 1
    for group in groups.values()
)

total_original = sum(original_counts.values())

if (
    counts["kept"]
    + counts["alternative_answer_records"]
    + counts["identical_answer_duplicates_skipped"]
    != total_original
):
    raise ValueError(
        "Kayıt muhasebesi uyuşmuyor."
    )

expected_kept = len(groups) - alternative_groups

if counts["kept"] != expected_kept:
    raise ValueError(
        "Benzersiz soru sayısı uyuşmuyor."
    )

report = {
    "version": "v0.9",
    "status": "provisional_not_training_approved",
    "original_records": total_original,
    "unique_questions": len(groups),
    "alternative_answer_groups": alternative_groups,
    "identical_answer_groups": identical_groups,
    "counts": dict(counts),
    "kept_per_split": dict(kept_by_split),
    "original_per_split": dict(original_counts),
    "limitations": [
        "Farklı cevaplar mutlaka hukuken çelişkili değildir.",
        "Tek cevaplı kayıtların hukuki doğruluğu onaylanmadı.",
        "Yakın anlamlı sorular ayrıca incelenmelidir.",
        "Kaynak ve lisans incelemesi tamamlanmadı.",
        "Split dağılımının hukuk alanlarına göre dengesizliği sürüyor."
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

print("LEXITECH TR - GÜVENLİ TEKRAR AYIRMA")
print("=" * 60)

print("Orijinal kayıt:", total_original)
print("Benzersiz soru:", len(groups))
print("Farklı cevaplı soru grubu:", alternative_groups)
print("Aynı cevaplı tekrar grubu:", identical_groups)

print(
    "\nİncelemeye ayrılan farklı cevaplı kayıt:",
    counts["alternative_answer_records"]
)

print(
    "Atlanan birebir eşdeğer tekrar:",
    counts["identical_answer_duplicates_skipped"]
)

print("\nÖN TASLAK DAĞILIMI")

for split in SPLITS:
    print(
        f"{split}: {kept_by_split[split]:,}"
    )

print("\nÖn taslak toplamı:", counts["kept"])
print("Kümeler arası aynı soru:", len(leaked))
print("Rapor:", REPORT)
print("Alternatif cevap havuzu:", QUARANTINE)
print("Yeni veri klasörü:", OUTPUT)
print("Eski veri setleri değiştirilmedi.")
print("Hukuki doğruluk onayı verilmedi.")

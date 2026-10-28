import hashlib
import json
import re
import unicodedata

from pathlib import Path
from collections import Counter, defaultdict
from itertools import zip_longest

POOL = Path(
    "data/interim/instruction_citation_review_v0.9.jsonl"
)

AUDIT = Path(
    "data/interim/instruction_article_audit_v0.9.jsonl"
)

PLAN = Path(
    "reports/splits/instruction_split_plan_v0.9.json"
)

OUTPUT_DIR = Path(
    "data/final/instruction_v0.9"
)

REPORT = Path(
    "reports/quality/instruction_split_integrity_v0.9.json"
)

SPLITS = ("train", "validation", "test")


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def normalize_question(text):
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


plan = json.loads(PLAN.read_text(encoding="utf-8"))

document_splits = plan["document_splits"]
expected = plan["split_counts"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

# Önce geçici dosyalara yazacağız.
temporary_paths = {
    split: OUTPUT_DIR / f"{split}.jsonl.tmp"
    for split in SPLITS
}

handles = {
    split: temporary_paths[split].open(
        "w", encoding="utf-8"
    )
    for split in SPLITS
}

counts = Counter()
law_distribution = defaultdict(Counter)
source_distribution = defaultdict(Counter)

seen_ids = set()
question_owner = {}
document_owner = {}

errors = []

print("LEXITECH TR - INSTRUCTION DATASET v0.9")
print("=" * 60)

try:
    for candidate, audit in zip_longest(
        read_jsonl(POOL),
        read_jsonl(AUDIT)
    ):
        if candidate is None or audit is None:
            raise ValueError(
                "Aday ve madde denetim dosyalarının "
                "kayıt sayıları uyuşmuyor."
            )

        if str(candidate["id"]) != str(audit["id"]):
            raise ValueError(
                "Aday ve denetim kayıtlarının ID sırası bozuk."
            )

        if (
            audit["structural_status"]
            != "numbers_present_in_target_law"
        ):
            counts["reference_quarantine"] += 1
            continue

        if (
            candidate["source"]
            == "OrionCAF/turkish_law_qa_dataset"
        ):
            counts["source_quarantine"] += 1
            continue

        source_document = candidate.get(
            "source_document"
        )

        if not source_document:
            counts["missing_document_quarantine"] += 1
            continue

        source_document = str(source_document)

        if source_document not in document_splits:
            raise ValueError(
                f"Bölme planında belge yok: {source_document}"
            )

        split = document_splits[source_document]

        if split not in SPLITS:
            raise ValueError(f"Geçersiz split: {split}")

        record_id = str(candidate["id"])

        if record_id in seen_ids:
            errors.append(
                f"Tekrarlanan kayıt ID: {record_id}"
            )

        seen_ids.add(record_id)

        question = candidate["question"].strip()
        answer = candidate["answer"].strip()

        normalized = normalize_question(question)

        previous_split = question_owner.get(normalized)

        if previous_split is not None:
            if previous_split != split:
                errors.append(
                    f"Kümeler arası aynı soru: {record_id}"
                )
            else:
                counts["same_question_within_split"] += 1
        else:
            question_owner[normalized] = split

        previous_doc_split = document_owner.get(
            source_document
        )

        if (
            previous_doc_split is not None
            and previous_doc_split != split
        ):
            errors.append(
                f"Kaynak belge sızıntısı: {source_document}"
            )

        document_owner[source_document] = split

        if not question or not answer:
            errors.append(
                f"Boş soru veya cevap: {record_id}"
            )
            continue

        law = str(candidate["law_indicator"])

        record = {
            "id": record_id,
            "messages": [
                {
                    "role": "user",
                    "content": question
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ],
            "metadata": {
                "dataset_version": "v0.9",
                "language": "tr",
                "domain": "law",
                "law_indicator": law,
                "source": candidate["source"],
                "source_document": source_document,
                "split": split,
                "source_verified": False,
                "legal_accuracy_verified": False,
                "citation_accuracy_verified": False,
                "rights_status": "pending_review",
                "training_approved": False,
                "quality_status": "requires_review",
                "selection_method": "heuristic_v0.9"
            }
        }

        handles[split].write(
            json.dumps(
                record,
                ensure_ascii=False
            ) + "\n"
        )

        counts[split] += 1
        law_distribution[split][law] += 1
        source_distribution[split][
            candidate["source"]
        ] += 1

finally:
    for handle in handles.values():
        handle.close()

for split in SPLITS:
    if counts[split] != expected[split]:
        errors.append(
            f"{split}: beklenen {expected[split]}, "
            f"oluşan {counts[split]}"
        )

if sum(counts[s] for s in SPLITS) != 129152:
    errors.append("Toplam kayıt sayısı uyuşmuyor.")

report = {
    "status": "PASS" if not errors else "FAIL",
    "dataset_version": "v0.9",
    "training_approved": False,
    "counts": dict(counts),
    "law_distribution": {
        split: dict(values)
        for split, values in law_distribution.items()
    },
    "source_distribution": {
        split: dict(values)
        for split, values in source_distribution.items()
    },
    "distinct_source_documents": len(document_owner),
    "distinct_normalized_questions": len(question_owner),
    "integrity_error_count": len(errors),
    "errors": errors[:30],
    "limitations": [
        "Hukuki doğruluk henüz onaylanmadı.",
        "Kullanım hakları ve lisanslar inceleniyor.",
        "Yakın tekrarlar arasında sızıntı olabilir.",
        "Madde numarası varlığı doğruluk kanıtı değildir.",
        "Kaynak belge adları resmi kanun belgeleri değildir."
    ]
}

REPORT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

if errors:
    print("\nHATA: Bütünlük kontrolü başarısız.")
    for error in errors[:15]:
        print(error)
    print("Geçici dosyalar korundu.")
    raise SystemExit(1)

# Kontroller başarılıysa geçici dosyaları kesin adlarına taşı.
for split in SPLITS:
    temporary_paths[split].replace(
        OUTPUT_DIR / f"{split}.jsonl"
    )

print("\nOLUŞTURULAN VERİ SETLERİ")
print("-" * 60)

for split in SPLITS:
    print(f"{split}: {counts[split]:,} kayıt")
    print("  Dosya:", OUTPUT_DIR / f"{split}.jsonl")

print("\nTOPLAM:", sum(counts[s] for s in SPLITS))
print("Farklı kaynak dosyası:", len(document_owner))
print(
    "Farklı normalize soru:",
    len(question_owner)
)
print(
    "Küme içindeki tekrarlı soru:",
    counts["same_question_within_split"]
)
print("Bütünlük hatası:", len(errors))
print("Sonuç:", report["status"])
print("Rapor:", REPORT)

print("\nKANUN BAZINDA DAĞILIM")
for split in SPLITS:
    print(f"\n{split}:")
    for law, count in sorted(
        law_distribution[split].items()
    ):
        print(f"  {law}: {count:,}")

print("\nBu dosyalar eğitim için henüz onaylı değildir.")
print("Önceki veri setleri değiştirilmedi.")

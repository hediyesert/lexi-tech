import json
from pathlib import Path
from collections import Counter

INPUT = Path("data/deduplicated/exact_unique.jsonl")
OUTPUT = Path(
    "reports/quality/instruction_candidate_audit_v0.9.json"
)

counts = Counter()
sources = Counter()
missing_by_source = {}
examples = {}
seen_ids = set()

print("LEXITECH TR - INSTRUCTION DATASET ÖN DENETİMİ")
print("=" * 60)

with INPUT.open(encoding="utf-8") as f:
    for line_number, line in enumerate(f, 1):
        if not line.strip():
            continue

        record = json.loads(line)
        counts["total"] += 1

        source = str(record.get("source") or "unknown")
        sources[source] += 1

        question = record.get("question")
        answer = record.get("answer")
        doc = record.get("source_document")
        record_id = record.get("id")

        question = question.strip() if isinstance(question, str) else ""
        answer = answer.strip() if isinstance(answer, str) else ""

        if not question:
            counts["empty_question"] += 1

        if not answer:
            counts["empty_answer"] += 1

        if not doc or not str(doc).strip():
            counts["missing_source_document"] += 1
            missing_by_source[source] = (
                missing_by_source.get(source, 0) + 1
            )

        if not record_id:
            counts["missing_id"] += 1
        elif record_id in seen_ids:
            counts["duplicate_id"] += 1
        else:
            seen_ids.add(record_id)

        if question and len(question) < 15:
            counts["short_question_under_15_chars"] += 1

        if answer and len(answer) < 30:
            counts["short_answer_under_30_chars"] += 1

        if question and len(question) > 3000:
            counts["long_question_over_3000_chars"] += 1

        if answer and len(answer) > 10000:
            counts["long_answer_over_10000_chars"] += 1

        if source not in examples:
            examples[source] = []

        if len(examples[source]) < 2:
            examples[source].append({
                "id": str(record_id),
                "question_preview": question[:180],
                "answer_preview": answer[:250],
                "source_document": str(doc)[:150],
                "metadata_type": type(
                    record.get("metadata")
                ).__name__
            })

report = {
    "input": str(INPUT),
    "counts": dict(counts),
    "sources": dict(sources),
    "missing_source_document_by_source": missing_by_source,
    "examples": examples,
    "status": "automatic_screening_only"
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Toplam kayıt:", counts["total"])
print("\nKAYNAK DAĞILIMI")

for source, count in sources.most_common():
    print(f"  {source}: {count:,}")

print("\nİLK KALİTE KONTROLLERİ")

for key in [
    "empty_question",
    "empty_answer",
    "missing_source_document",
    "missing_id",
    "duplicate_id",
    "short_question_under_15_chars",
    "short_answer_under_30_chars",
    "long_question_over_3000_chars",
    "long_answer_over_10000_chars"
]:
    print(f"  {key}: {counts[key]:,}")

print("\nKAYNAK BAZINDA ÖRNEKLER")

for source, items in examples.items():
    print(f"\nKaynak: {source}")

    for item in items:
        print("  Soru:", item["question_preview"])
        print("  Cevap:", item["answer_preview"])
        print("  Kaynak belge:", item["source_document"])
        print("  Metadata türü:", item["metadata_type"])
        print()

print("Rapor:", OUTPUT)
print("Hiçbir veri kaydı değiştirilmedi.")
print("Hukuki doğruluk henüz denetlenmedi.")

import json
import re
import unicodedata
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path("data/final/instruction_v0.9")

REPORT = Path(
    "reports/quality/instruction_duplicate_questions_v0.9.json"
)

SPLITS = ("train", "validation", "test")


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


questions = defaultdict(list)
counts = Counter()

for split in SPLITS:
    for record in read_jsonl(ROOT / f"{split}.jsonl"):
        question = record["messages"][0]["content"]
        answer = record["messages"][1]["content"]

        normalized_question = normalize(question)

        questions[normalized_question].append({
            "id": record["id"],
            "split": split,
            "law": str(
                record["metadata"]["law_indicator"]
            ),
            "source_document": record["metadata"][
                "source_document"
            ],
            "answer": answer,
            "normalized_answer": normalize(answer),
            "question": question
        })

        counts["total"] += 1

duplicate_groups = []
different_answer_examples = []

for question, records in questions.items():
    if len(records) == 1:
        continue

    counts["duplicate_question_groups"] += 1
    counts["additional_duplicate_records"] += (
        len(records) - 1
    )

    answers = {
        item["normalized_answer"]
        for item in records
    }

    splits = {
        item["split"]
        for item in records
    }

    laws = {
        item["law"]
        for item in records
    }

    if len(answers) == 1:
        counts["groups_with_identical_answers"] += 1
    else:
        counts["groups_with_different_answers"] += 1

        if len(different_answer_examples) < 8:
            different_answer_examples.append({
                "question": records[0]["question"],
                "record_count": len(records),
                "answers": [
                    {
                        "id": item["id"],
                        "law": item["law"],
                        "source_document": item["source_document"],
                        "answer": item["answer"][:700]
                    }
                    for item in records[:3]
                ]
            })

    if len(splits) > 1:
        counts["cross_split_exact_question_groups"] += 1

    if len(laws) > 1:
        counts["groups_with_multiple_law_labels"] += 1

    duplicate_groups.append({
        "question": records[0]["question"][:150],
        "record_count": len(records),
        "distinct_answer_count": len(answers),
        "splits": sorted(splits),
        "laws": sorted(laws)
    })

report = {
    "status": "automatic_audit_only",
    "counts": dict(counts),
    "top_repeated_questions": sorted(
        duplicate_groups,
        key=lambda x: -x["record_count"]
    )[:15],
    "different_answer_examples": different_answer_examples,
    "note": (
        "Farklı cevaplar mutlaka çelişkili değildir. "
        "Hukuki anlam ve doğruluk ayrıca incelenmelidir."
    )
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

print("LEXITECH TR - TEKRARLI SORU DENETİMİ")
print("=" * 60)

print("Toplam kayıt:", counts["total"])
print("Farklı soru:", len(questions))
print(
    "Tekrarlanan soru grubu:",
    counts["duplicate_question_groups"]
)
print(
    "Fazladan tekrar kaydı:",
    counts["additional_duplicate_records"]
)
print(
    "Cevapları aynı olan grup:",
    counts["groups_with_identical_answers"]
)
print(
    "Cevapları farklı olan grup:",
    counts["groups_with_different_answers"]
)
print(
    "Farklı splitlerde aynı soru:",
    counts["cross_split_exact_question_groups"]
)
print(
    "Farklı kanun etiketi bulunan grup:",
    counts["groups_with_multiple_law_labels"]
)

print("\nFARKLI CEVAPLI İLK 5 ÖRNEK")
print("-" * 60)

for example in different_answer_examples[:5]:
    print("\nSORU:", example["question"])

    for item in example["answers"]:
        print("  Kaynak:", item["source_document"])
        print("  Kanun:", item["law"])
        print("  CEVAP:", item["answer"][:400])
        print()

print("\nRapor:", REPORT)
print("Hiçbir veri kaydı değiştirilmedi.")
print("Hukuki çelişki kontrolü henüz yapılmadı.")

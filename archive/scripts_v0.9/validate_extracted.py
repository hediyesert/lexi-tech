from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"

REQUIRED_FIELDS = {
    "id",
    "source",
    "source_split",
    "source_row",
    "source_document",
    "question",
    "answer",
    "metadata",
}


def validate_file(file_path):
    total = 0
    invalid_json = 0
    missing_fields = 0
    null_questions = 0
    null_answers = 0
    empty_questions = 0
    empty_answers = 0
    invalid_ids = 0

    ids = set()
    duplicate_ids = 0

    with open(file_path, "r", encoding="utf-8") as file:

        for line_number, line in enumerate(file, start=1):
            total += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                invalid_json += 1
                continue

            if not REQUIRED_FIELDS.issubset(record.keys()):
                missing_fields += 1

            record_id = record.get("id")

            if (
                not isinstance(record_id, str)
                or len(record_id) != 64
            ):
                invalid_ids += 1
            else:
                if record_id in ids:
                    duplicate_ids += 1
                else:
                    ids.add(record_id)

            question = record.get("question")
            answer = record.get("answer")

            if question is None:
                null_questions += 1
            elif not str(question).strip():
                empty_questions += 1

            if answer is None:
                null_answers += 1
            elif not str(answer).strip():
                empty_answers += 1

    return {
        "total": total,
        "invalid_json": invalid_json,
        "missing_fields": missing_fields,
        "null_questions": null_questions,
        "null_answers": null_answers,
        "empty_questions": empty_questions,
        "empty_answers": empty_answers,
        "invalid_ids": invalid_ids,
        "duplicate_ids": duplicate_ids,
        "unique_ids": len(ids),
    }


def main():

    files = sorted(EXTRACTED_DIR.glob("*/train.jsonl"))

    grand_total = 0

    for file_path in files:

        result = validate_file(file_path)
        grand_total += result["total"]

        print("\n" + "=" * 70)
        print(file_path.relative_to(PROJECT_ROOT))
        print("=" * 70)

        for key, value in result.items():
            print(f"{key}: {value}")

    print("\n" + "=" * 70)
    print(f"Toplam doğrulanan kayıt: {grand_total}")
    print("=" * 70)


if __name__ == "__main__":
    main()

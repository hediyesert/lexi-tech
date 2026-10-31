import csv
import json
from pathlib import Path

REVIEW = Path(
    "data/interim/instruction_language_manual_review_123_v0.9.csv"
)

DATA = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)

OUTPUT = Path(
    "data/interim/instruction_quality_quarantine_v0.9.csv"
)

if OUTPUT.exists():
    raise SystemExit(
        "İnceleme listesi zaten mevcut; üzerine yazılmadı: "
        + str(OUTPUT)
    )

with REVIEW.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 123:
    raise ValueError("123 dil inceleme kaydı bekleniyordu.")

issues = []

for row in rows:
    for field, flag_column in (
        ("question", "question_quality_flag"),
        ("answer", "answer_quality_flag"),
    ):
        flag = row.get(flag_column, "").strip()

        if flag:
            issues.append({
                "review_number": int(row["review_number"]),
                "record_id": row["record_id"],
                "split": row["split"],
                "affected_field": field,
                "quality_flag": flag,
            })

if len(issues) != 2:
    raise ValueError(
        f"2 kalite sorunu bekleniyordu: {len(issues)}"
    )

expected = {
    (36, "answer", "citation_only_answer"),
    (120, "question", "incomplete_question_fragment"),
}

actual = {
    (
        item["review_number"],
        item["affected_field"],
        item["quality_flag"],
    )
    for item in issues
}

if actual != expected:
    raise ValueError(
        "Kalite sorunlarının alanları beklenenden farklı."
    )

wanted = {item["record_id"] for item in issues}
found = {}

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)

            if record["id"] in wanted:
                if record["id"] in found:
                    raise ValueError(
                        "Kayıt birden fazla split içinde bulundu."
                    )

                found[record["id"]] = {
                    "split": split,
                    "record": record,
                }

if set(found) != wanted:
    raise ValueError(
        "Kalite sorunu bulunan kayıtların tümü bulunamadı."
    )

queue = []

for item in sorted(
    issues, key=lambda x: x["review_number"]
):
    located = found[item["record_id"]]

    if located["split"] != item["split"]:
        raise ValueError(
            "Kayıt split bilgisi inceleme dosyasıyla uyuşmuyor."
        )

    record = located["record"]

    if item["affected_field"] == "question":
        text = record["messages"][0]["content"]
    else:
        text = record["messages"][1]["content"]

    queue.append({
        "record_id": item["record_id"],
        "split": item["split"],
        "affected_field": item["affected_field"],
        "quality_flag": item["quality_flag"],
        "text_length": len(text),
        "review_status": "pending",
        "recommended_action": "manual_review_before_training",
        "final_decision": "",
        "decision_reason": "",
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(queue[0].keys())
    )
    writer.writeheader()
    writer.writerows(queue)

print("LEXITECH TR - INSTRUCTION KALITE INCELEME LISTESI")
print("=" * 60)
print("Tespit edilen sorunlu QA:", len(queue))

for item in queue:
    print("\nSorun:", item["quality_flag"])
    print("Alan:", item["affected_field"])
    print("Split:", item["split"])
    print("Metin uzunluğu:", item["text_length"])
    print("Karar durumu:", item["review_status"])

print("\nListe:", OUTPUT)
print("Egitim onayi verilen kayit: 0")
print("Kayitlar silinmedi veya duzeltilmedi.")
print("Ana veri setleri degistirilmedi.")

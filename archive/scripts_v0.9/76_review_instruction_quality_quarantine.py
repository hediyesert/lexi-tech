import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_quality_quarantine_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_quality_quarantine_before_review_v0.9.csv"
)

REASONS = {
    "citation_only_answer": (
        "Cevap yalnızca madde atfı ve URL içeriyor; "
        "soruyu yeterli biçimde yanıtlamıyor."
    ),
    "incomplete_question_fragment": (
        "Soru alanı tamamlanmış soru yerine "
        "konu başlığı içeriyor."
    ),
}

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten mevcut; işlem yapılmadı: "
        + str(BACKUP)
    )

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = list(reader.fieldnames or [])
    rows = list(reader)

if len(rows) != 2:
    raise ValueError(
        f"2 kalite kaydı bekleniyordu: {len(rows)}"
    )

if set(row["quality_flag"] for row in rows) != set(REASONS):
    raise ValueError("Beklenmeyen kalite uyarısı bulundu.")

if len({row["record_id"] for row in rows}) != 2:
    raise ValueError("Kayıt kimlikleri tekrarlı.")

for row in rows:
    if row["review_status"] != "pending":
        raise ValueError("Önceden değerlendirilmiş kayıt bulundu.")

    if row["final_decision"].strip():
        raise ValueError("Nihai karar alanı önceden doldurulmuş.")

shutil.copy2(PATH, BACKUP)

for row in rows:
    row["review_status"] = "assistant_recommended_quarantine"
    row["recommended_action"] = (
        "exclude_from_future_training_until_corrected_and_verified"
    )
    row["decision_reason"] = REASONS[row["quality_flag"]]

    # Bu alan yalnızca nihai insan kararı için.
    row["final_decision"] = ""

temporary = PATH.with_suffix(".csv.tmp")

with temporary.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

temporary.replace(PATH)

status = Counter(row["review_status"] for row in rows)

print("LEXITECH TR - KALITE KARANTINA ONERILERI")
print("=" * 60)
print("Incelenen kayit:", len(rows))
print(
    "Gecici karantina onerisi:",
    status["assistant_recommended_quarantine"]
)
print(
    "Nihai insan karari:",
    sum(bool(row["final_decision"]) for row in rows)
)

for row in rows:
    print("\nSorun:", row["quality_flag"])
    print("Etkilenen alan:", row["affected_field"])
    print("Oneri:", row["recommended_action"])

print("\nYedek:", BACKUP)
print("Guncellenen liste:", PATH)
print("Ana veri setleri degistirilmedi.")
print("Egitim verisinden fiziksel cikarma yapilmadi.")

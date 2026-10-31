import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_language_manual_review_123_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_language_manual_review_123_before_final24_v0.9.csv"
)

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten var; hiçbir dosya değiştirilmedi: "
        + str(BACKUP)
    )

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 123:
    raise ValueError("123 satırlık dosya bekleniyordu.")

numbers = sorted(int(row["review_number"]) for row in rows)

if numbers != list(range(1, 124)):
    raise ValueError("Kayıt numaraları uyuşmuyor.")

previous = sum(
    row["review_status"] == "assistant_preliminary"
    for row in rows
)

if previous != 99:
    raise ValueError(
        f"99 önceki değerlendirme bekleniyordu: {previous}"
    )

for row in rows:
    n = int(row["review_number"])

    if 100 <= n <= 123:
        if row["review_status"] != "pending":
            raise ValueError(
                f"{n}. kayıt önceden değerlendirilmiş."
            )

        if row["automatic_category"] != "uncertain_short":
            raise ValueError(
                f"{n}. kayıt kısa metin kategorisinde değil."
            )

        if row["text_field"] != "question":
            raise ValueError(
                f"{n}. kayıt soru alanına ait değil."
            )

shutil.copy2(PATH, BACKUP)

for row in rows:
    n = int(row["review_number"])

    if 100 <= n <= 123:
        row["assistant_language_assessment"] = "tr"
        row["review_status"] = "assistant_preliminary"

        row["notes"] = (
            "Metin Turkce gorunuyor. Kisa metin nedeniyle "
            "otomatik dil tespiti belirsiz. "
            "Hukuki cevap dogrulanmadi."
        )

        if n == 108:
            row["notes"] = (
                "Turkce soru; mobbing yabanci kokenli "
                "bir terim. Hukuki cevap dogrulanmadi."
            )

        if n == 120:
            row["question_quality_flag"] = (
                "incomplete_question_fragment"
            )
            row["notes"] = (
                "Metin Turkce, ancak 'Zimmet Sucuna "
                "Yardim Etme' tam bir soru degil. "
                "Ayri soru kalitesi incelemesi gerekli."
            )

temporary = PATH.with_suffix(".csv.tmp")

with temporary.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

temporary.replace(PATH)

statuses = Counter(
    row["review_status"] for row in rows
)

languages = Counter(
    row["assistant_language_assessment"] for row in rows
)

quality = [
    row for row in rows
    if row["question_quality_flag"].strip()
]

print("LEXITECH TR - DIL INCELEMESI TAMAMLANDI")
print("=" * 60)
print("Toplam supheli metin:", len(rows))
print(
    "Asistan on degerlendirmesi tamamlanan:",
    statuses["assistant_preliminary"]
)
print("Turkce gorunen:", languages["tr"])
print(
    "Dil durumu ayri isaretlenen:",
    languages["not_assessable"]
)
print("Bekleyen:", statuses["pending"])
print("Soru kalitesi uyarisi:", len(quality))

for row in quality:
    print(
        "  Kayit",
        row["review_number"],
        ":",
        row["question_quality_flag"]
    )

print("\nYedek:", BACKUP)
print("Guncellenen:", PATH)
print("Bagimsiz uzman onayi: 0")
print("Ana veri setleri degistirilmedi.")

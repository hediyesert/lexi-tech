import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_language_manual_review_123_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_language_manual_review_123_before_batch4_v0.9.csv"
)

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 123:
    raise ValueError("123 kayıtlık inceleme dosyası bekleniyordu.")

numbers = sorted(int(row["review_number"]) for row in rows)

if numbers != list(range(1, 124)):
    raise ValueError("İnceleme numaraları beklenenden farklı.")

previous = sum(
    row["review_status"] == "assistant_preliminary"
    for row in rows
)

if previous != 74:
    raise ValueError(
        f"74 önceki değerlendirme bekleniyordu: {previous}"
    )

for row in rows:
    number = int(row["review_number"])

    if 75 <= number <= 99:
        if row["review_status"] != "pending":
            raise ValueError(
                f"{number}. kayıt daha önce değerlendirilmiş."
            )

        if row["automatic_category"] != "uncertain_short":
            raise ValueError(
                f"{number}. kayıt kısa metin kategorisinde değil."
            )

        if row["text_field"] != "question":
            raise ValueError(
                f"{number}. kayıt soru alanına ait değil."
            )

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten mevcut; işlem yapılmadı: "
        + str(BACKUP)
    )

shutil.copy2(PATH, BACKUP)

for row in rows:
    number = int(row["review_number"])

    if 75 <= number <= 99:
        row["assistant_language_assessment"] = "tr"
        row["review_status"] = "assistant_preliminary"

        if number == 96:
            row["notes"] = (
                "Turkce soru; Ne bis in idem Latince hukuk "
                "terimidir. Yalnizca dil incelendi."
            )
        else:
            row["notes"] = (
                "Soru Turkce olarak degerlendirildi. "
                "Otomatik belirsizlik kisa metinden "
                "kaynaklaniyor. Hukuki dogruluk incelenmedi."
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

print("LEXITECH TR - DIL INCELEMESI / PARTI 4 KAYDI")
print("=" * 60)

print("Toplam supheli metin:", len(rows))
print(
    "On degerlendirme tamamlanan:",
    statuses["assistant_preliminary"]
)
print("Turkce gorunen:", languages["tr"])
print(
    "Ayri kalite incelemesi:",
    languages["not_assessable"]
)
print("Bekleyen:", statuses["pending"])

print("\nYedek:", BACKUP)
print("Guncellenen dosya:", PATH)
print("Bagimsiz uzman onayi: 0")
print("Ana veri setleri degistirilmedi.")

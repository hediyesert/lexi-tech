import csv
import shutil
from pathlib import Path
from collections import Counter

PATH = Path(
    "data/interim/instruction_language_manual_review_123_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_language_manual_review_123_before_batch3_v0.9.csv"
)

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 123:
    raise ValueError("123 satırlık dil inceleme dosyası bekleniyordu.")

numbers = sorted(int(row["review_number"]) for row in rows)

if numbers != list(range(1, 124)):
    raise ValueError("İnceleme numaraları beklenenden farklı.")

previously_reviewed = sum(
    row["review_status"] == "assistant_preliminary"
    for row in rows
)

if previously_reviewed != 49:
    raise ValueError(
        f"49 önceki değerlendirme bekleniyordu: {previously_reviewed}"
    )

for row in rows:
    number = int(row["review_number"])

    if 50 <= number <= 74:
        if row["review_status"] != "pending":
            raise ValueError(f"{number}. kayıt zaten değerlendirilmiş.")

        if row["automatic_category"] != "uncertain_short":
            raise ValueError(
                f"{number}. kayıt kısa metin kategorisinde değil."
            )

        if row["text_field"] != "question":
            raise ValueError(
                f"{number}. kaydın incelenen alanı farklı."
            )

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten mevcut, dosya değiştirilmedi: " + str(BACKUP)
    )

shutil.copy2(PATH, BACKUP)

for row in rows:
    number = int(row["review_number"])

    if 50 <= number <= 74:
        row["assistant_language_assessment"] = "tr"
        row["review_status"] = "assistant_preliminary"
        row["notes"] = (
            "Soru metni Turkce olarak degerlendirildi. "
            "Otomatik belirsizlik 30 karakter esiginden "
            "kaynaklaniyor. Hukuki cevap dogrulanmadi."
        )

temporary = PATH.with_suffix(".csv.tmp")

with temporary.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

temporary.replace(PATH)

status = Counter(row["review_status"] for row in rows)
language = Counter(
    row["assistant_language_assessment"] for row in rows
)

print("LEXITECH TR - DIL INCELEMESI / PARTI 3 KAYDI")
print("=" * 60)
print("Toplam supheli metin:", len(rows))
print("On degerlendirme tamamlanan:", status["assistant_preliminary"])
print("Turkce gorunen:", language["tr"])
print("Ayri kalite incelemesi:", language["not_assessable"])
print("Bekleyen:", status["pending"])
print("Yedek:", BACKUP)
print("Guncellenen dosya:", PATH)
print("Bagimsiz uzman onayi: 0")
print("Ana veri setleri degistirilmedi.")

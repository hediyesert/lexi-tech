import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_task_independent_review_50_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_task_independent_review_50_before_final10_v0.9.csv"
)

REVIEWS = {
    41: (
        "article_explanation",
        "6706 sayılı Kanun'un 17. maddesinin kapsamı soruluyor."
    ),
    42: (
        "article_explanation",
        "TMK m. 52'nin düzenlediği konu soruluyor."
    ),
    43: (
        "case_application",
        "Somut suç olayında TCK m. 53/5'in uygulanması soruluyor."
    ),
    44: (
        "article_explanation",
        "Anayasal dayanak ve ilgili maddenin içeriği soruluyor."
    ),
    45: (
        "article_explanation",
        "CMK m. 188/1'in içeriği ve ihlalinin önemi soruluyor."
    ),
    46: (
        "article_explanation",
        "TCK m. 210'un özel düzenlemesi soruluyor."
    ),
    47: (
        "legal_conditions",
        "Cezayı artıran nitelikli hallerin koşulları soruluyor."
    ),
    48: (
        "case_application",
        "Mirasın reddi olayında alacaklıların hukuki imkânları soruluyor."
    ),
    49: (
        "case_application",
        "Somut ihale olayına TCK m. 235'in uygulanması soruluyor."
    ),
    50: (
        "comparison",
        "İki CMK hükmü arasındaki ilişki karşılaştırılıyor."
    ),
}

EXPECTED = {
    **{n: "article_explanation" for n in range(41, 46)},
    **{n: "other" for n in range(46, 51)},
}

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten mevcut; işlem yapılmadı: "
        + str(BACKUP)
    )

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 50:
    raise ValueError("50 satırlık test dosyası bekleniyordu.")

numbers = sorted(int(row["review_number"]) for row in rows)

if numbers != list(range(1, 51)):
    raise ValueError("Kayıt numaraları beklenenden farklı.")

previous = [
    row for row in rows
    if row["reviewer_label"].strip()
]

if len(previous) != 40:
    raise ValueError(
        f"Önceden 40 kayıt bekleniyordu: {len(previous)}"
    )

for row in rows:
    number = int(row["review_number"])

    if number in REVIEWS:
        if row["predicted_label"] != EXPECTED[number]:
            raise ValueError(
                f"{number}. kaydın otomatik etiketi beklenenden farklı."
            )

        if row["reviewer_label"].strip():
            raise ValueError(
                f"{number}. kayıt zaten değerlendirilmiş."
            )

shutil.copy2(PATH, BACKUP)

for row in rows:
    number = int(row["review_number"])

    if number in REVIEWS:
        label, reason = REVIEWS[number]

        row["reviewer_label"] = label
        row["review_status"] = "assistant_proposed"
        row["reviewer_notes"] = (
            reason
            + " Asistanın birincil görev etiketi önerisidir. "
            + "Bağımsız uzman onayı ve hukuki cevap doğrulaması yoktur."
        )

temporary = PATH.with_suffix(".csv.tmp")

with temporary.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

temporary.replace(PATH)

reviewed = [
    row for row in rows
    if row["reviewer_label"].strip()
]

status = Counter(
    "same" if row["predicted_label"] == row["reviewer_label"]
    else "different"
    for row in reviewed
)

print("LEXITECH TR - 50 SORULUK GÖREV TESTİ")
print("=" * 60)
print("Toplam test sorusu:", len(rows))
print("Asistan etiketi önerilen:", len(reviewed))
print("Kalan:", len(rows) - len(reviewed))
print("Otomatik etiketle uyumlu:", status["same"])
print("Değişiklik önerilen:", status["different"])

print(
    "Etiket uyumu:",
    f"%{status['same'] / len(reviewed) * 100:.2f}"
)

print("\nYedek:", BACKUP)
print("Güncellenen dosya:", PATH)

print("\nBağımsız insan uzman onayı: 0")
print("Hukuki cevap doğrulaması: yapılmadı")
print("Ana veri setleri değiştirilmedi.")

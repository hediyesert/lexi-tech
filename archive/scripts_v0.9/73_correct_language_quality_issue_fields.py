import csv
import shutil
from pathlib import Path
from collections import Counter

PATH = Path(
    "data/interim/instruction_language_manual_review_123_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_language_manual_review_123_before_field_fix_v0.9.csv"
)

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten var, işlem yapılmadı: " + str(BACKUP)
    )

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = list(reader.fieldnames or [])
    rows = list(reader)

if len(rows) != 123:
    raise ValueError("123 inceleme kaydı bekleniyordu.")

if "question_quality_flag" not in fields:
    raise ValueError("Mevcut kalite sütunu bulunamadı.")

if "answer_quality_flag" in fields:
    raise ValueError("Düzeltme daha önce uygulanmış olabilir.")

lookup = {
    int(row["review_number"]): row
    for row in rows
}

row36 = lookup[36]
row120 = lookup[120]

if (
    row36["text_field"] != "answer"
    or row36["question_quality_flag"]
       != "source_url_contamination"
):
    raise ValueError("36. kayıt beklenenden farklı.")

if (
    row120["text_field"] != "question"
    or row120["question_quality_flag"]
       != "incomplete_question_fragment"
):
    raise ValueError("120. kayıt beklenenden farklı.")

shutil.copy2(PATH, BACKUP)

fields.insert(
    fields.index("question_quality_flag") + 1,
    "answer_quality_flag"
)

for row in rows:
    row["answer_quality_flag"] = ""

row36["answer_quality_flag"] = (
    "citation_only_answer"
)
row36["question_quality_flag"] = ""
row36["notes"] = (
    "Cevap TCK md. 211 ve kaynak URL'sinden "
    "olusuyor; soruya yeterli hukuki aciklama "
    "sunmuyor. Cevap kalitesi incelemesi gerekli. "
    "Dil ve hukuki dogruluk bagimsiz onayli degil."
)

row120["notes"] = (
    "Soru Turkce, ancak tamamlanmis bir soru "
    "yerine konu basligi niteliginde. "
    "Soru kalitesi incelemesi gerekli."
)

TEMP = PATH.with_suffix(".csv.tmp")

with TEMP.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

TEMP.replace(PATH)

question_flags = Counter(
    row["question_quality_flag"]
    for row in rows
    if row["question_quality_flag"]
)

answer_flags = Counter(
    row["answer_quality_flag"]
    for row in rows
    if row["answer_quality_flag"]
)

print("LEXITECH TR - KALITE ALANI DUZELTMESI")
print("=" * 55)
print("Toplam inceleme kaydi:", len(rows))

print("\nSORU KALITESI")
print(dict(question_flags))

print("\nCEVAP KALITESI")
print(dict(answer_flags))

print("\n36. kaydin sorunlu alani:", row36["text_field"])
print("36. kaydin cevap uyarisi:", row36["answer_quality_flag"])

print("\n120. kaydin sorunlu alani:", row120["text_field"])
print("120. kaydin soru uyarisi:", row120["question_quality_flag"])

print("\nYedek:", BACKUP)
print("Guncellenen:", PATH)
print("Ana veri setleri degistirilmedi.")
print("Onceki dil raporu yeni alanlara gore guncellenmeli.")

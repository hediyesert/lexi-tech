import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_task_independent_review_50_v0.9.csv"
)
BACKUP = PATH.with_name(
    "instruction_task_independent_review_50_before_next20_v0.9.csv"
)

REVIEWS = {
    21: ("procedure_deadline", "İhtiyati hacze itiraz süresi ve kanun yolu."),
    22: ("procedure_deadline", "Temyiz dilekçesindeki eksikliğin usuli sonucu."),
    23: ("procedure_deadline", "Rehinli alacakta takip yolunun seçilmesi."),
    24: ("procedure_deadline", "Tazminat davası açma süresi."),
    25: ("procedure_deadline", "Mülkiyetin dönüştürülmesi davasındaki karar usulü."),

    26: ("legal_conditions", "Haksız tahrik koşulları."),
    27: ("legal_conditions", "Ceza indirimi için gereken illiyet ilişkisi."),
    28: ("legal_conditions", "Adli sicil kaydının silinme koşulları."),
    29: ("legal_conditions", "Cezalandırma ve etkin pişmanlık koşulları."),
    30: ("legal_conditions", "Yürütmenin durdurulması koşulları."),

    31: ("penalty_sanction", "Taksirle yaralamanın cezası."),
    32: ("penalty_sanction", "Belirli suçun cezası."),
    33: ("penalty_sanction", "Sendikal hakların engellenmesinin cezası."),
    34: ("penalty_sanction", "Soybağını değiştirme suçunun cezası."),
    35: ("penalty_sanction", "Basit zimmet suçunun cezası."),

    36: ("penalty_sanction", "Failin yetkisine bağlı ceza değişikliği."),
    37: ("comparison", "Boşanma türleri arasındaki temel ayrım."),
    38: ("procedure_deadline", "Mahkeme müzakeresinin yönetim usulü."),
    39: ("procedure_deadline", "Merciin karar verme süresi."),
    40: ("definition", "Yasal önalım hakkının tanımı ve kapsamı."),
}

EXPECTED = {
    **{n: "procedure_deadline" for n in range(21, 26)},
    **{n: "legal_conditions" for n in range(26, 31)},
    **{n: "penalty_sanction" for n in range(31, 36)},
    **{n: "definition" for n in range(36, 41)},
}

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten var; işlem yapılmadı: " + str(BACKUP)
    )

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 50:
    raise ValueError("50 satırlık test dosyası bekleniyordu.")

if sorted(int(r["review_number"]) for r in rows) != list(range(1, 51)):
    raise ValueError("Kayıt numaraları beklenenden farklı.")

previous = [
    r for r in rows
    if r["reviewer_label"].strip()
]

if len(previous) != 20:
    raise ValueError(
        f"Önceden değerlendirilmiş 20 kayıt bekleniyordu: {len(previous)}"
    )

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        if row["predicted_label"] != EXPECTED[n]:
            raise ValueError(f"{n}. kaydın otomatik etiketi farklı.")

        if row["reviewer_label"].strip():
            raise ValueError(f"{n}. kayıt önceden değerlendirilmiş.")

shutil.copy2(PATH, BACKUP)

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        label, reason = REVIEWS[n]
        row["reviewer_label"] = label
        row["review_status"] = "assistant_proposed"
        row["reviewer_notes"] = (
            reason
            + " Asistanın görev türü önerisidir; "
            + "bağımsız insan veya hukuk uzmanı onayı değildir."
        )

tmp = PATH.with_suffix(".csv.tmp")

with tmp.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(PATH)

reviewed = [
    r for r in rows
    if r["reviewer_label"].strip()
]

status = Counter(
    "same" if r["predicted_label"] == r["reviewer_label"]
    else "different"
    for r in reviewed
)

print("LEXITECH TR - YENİ TEST / İLK 40 KAYIT")
print("=" * 55)
print("Toplam test sorusu:", len(rows))
print("Asistan etiketi önerilen:", len(reviewed))
print("Kalan:", len(rows) - len(reviewed))
print("Otomatik etiketle uyumlu:", status["same"])
print("Değişiklik önerilen:", status["different"])
print("Yedek:", BACKUP)
print("Güncellenen dosya:", PATH)
print("Bağımsız insan uzman onayı: 0")
print("Ana veri setleri değiştirilmedi.")

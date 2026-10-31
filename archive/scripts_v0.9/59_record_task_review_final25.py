import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_task_type_review_70_v0.9.csv"
)
BACKUP = PATH.with_name(
    "instruction_task_type_review_70_before_final25_v0.9.csv"
)

# Numara: (önerilen birincil görev etiketi, gerekçe)
REVIEWS = {
    26: ("penalty_sanction", "Özel usulsüzlük cezasının miktarı ve sınırları."),
    27: ("procedure_deadline", "İcranın geri bırakılması başvuru usulü."),
    28: ("procedure_deadline", "Temyiz incelemesinin kapsamı."),
    29: ("procedure_deadline", "İstihkak iddiasında izlenecek usul."),
    30: ("case_application", "Somut olayda olağanüstü itirazın uygulanması."),
    31: ("legal_conditions", "Şikayetsiz yakalama koşulları."),
    32: ("legal_conditions", "Davanın reddedilme koşulları."),
    33: ("case_law_analysis", "Belirli Yargıtay kararında delil elde etme koşulları."),
    34: ("legal_conditions", "Kesin mühlette iflas sebepleri."),
    35: ("legal_conditions", "Gönüllü vazgeçme şartı."),
    36: ("definition", "SYOK kavramı ve verildiği durumlar."),
    37: ("legal_conditions", "Yoksulluk nafakası ve kusur şartları."),
    38: ("procedure_deadline", "Tahliye davası açma zamanı."),
    39: ("legal_conditions", "Rüşvet suçunun oluşma şartları."),
    40: ("case_law_analysis", "Yargıtay kararında casusluk unsurunun yorumu."),
    41: ("definition", "Trampa sözleşmesinin tanımı."),
    42: ("legal_conditions", "Basit yargılama usulünün istisnaları."),
    43: ("definition", "İhtiyaç sebebiyle tahliye davasının tanımı."),
    44: ("case_law_analysis", "Somut olay ve Yargıtay yaklaşımı."),
    45: ("case_law_analysis", "Yargıtay kararının yetki gerekçesi."),
    46: ("legal_conditions", "Komşuluk hukukundan doğan yükümlülük."),
    47: ("case_law_analysis", "Yargıtay kararındaki suç nitelendirmesi."),
    48: ("case_law_analysis", "Yargıtay'ın ceza artırımı hakkındaki görüşü."),
    49: ("case_application", "Somut polis memuru olayında nitelikli hal."),
    50: ("legal_conditions", "Cezayı artıran nitelikli halin kapsamı."),
}

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 70:
    raise ValueError("70 kayıtlık dosya bekleniyordu.")

expected = {
    **{i: "procedure_deadline" for i in range(26, 31)},
    **{i: "legal_conditions" for i in range(31, 41)},
    **{i: "definition" for i in range(41, 51)},
}

for row in rows:
    number = int(row["review_number"])

    if number in REVIEWS:
        if row["automatic_label"] != expected[number]:
            raise ValueError(f"{number}. kaydın etiketi beklenenden farklı.")

        if row["correct_label"].strip():
            raise ValueError(f"{number}. kayıt zaten değerlendirilmiş.")

previously_reviewed = sum(
    bool(row["correct_label"].strip()) for row in rows
)
if previously_reviewed != 45:
    raise ValueError(
        f"45 önceki değerlendirme bekleniyordu: {previously_reviewed}"
    )

if BACKUP.exists():
    raise SystemExit(
        "Yedek zaten mevcut; veri değiştirilmedi: " + str(BACKUP)
    )

shutil.copy2(PATH, BACKUP)

for row in rows:
    number = int(row["review_number"])

    if number in REVIEWS:
        correct_label, reason = REVIEWS[number]
        row["correct_label"] = correct_label
        row["label_correct"] = (
            "yes" if row["automatic_label"] == correct_label
            else "no"
        )
        row["review_notes"] = (
            reason
            + " Asistanın soru metninden önerdiği görev etiketi; "
            + "bağımsız uzman onayı ve hukuki doğruluk kontrolü yok."
        )

temp = PATH.with_suffix(".csv.tmp")
with temp.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

temp.replace(PATH)

status = Counter(row["label_correct"] for row in rows)
labels = Counter(row["correct_label"] for row in rows)

print("LEXITECH TR - 70 GÖREV TÜRÜ İNCELEMESİ")
print("=" * 55)
print("Toplam:", len(rows))
print("Etiket önerisi tamamlanan:", sum(labels.values()))
print("Otomatik etiketi uygun bulunan:", status["yes"])
print("Değiştirilmesi önerilen:", status["no"])
print("Boş kalan:", sum(not row["correct_label"] for row in rows))

print("\nÖNERİLEN GÖREV TÜRLERİ")
for label, count in labels.most_common():
    print(f"{label:<25} {count:>3}")

print("\nYedek:", BACKUP)
print("Güncellenen dosya:", PATH)
print("Bağımsız uzman onayı yapılmadı.")
print("Ana veri setleri değiştirilmedi.")

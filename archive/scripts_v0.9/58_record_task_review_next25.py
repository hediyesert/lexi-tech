import csv
import shutil
from pathlib import Path
from collections import Counter

PATH = Path(
    "data/interim/instruction_task_type_review_70_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_task_type_review_70_before_next25_v0.9.csv"
)

REVIEWS = {
    1: ("comparison", "Doğrudan verilen ve çevrilen adli para cezasının infazı karşılaştırılıyor."),
    2: ("comparison", "Zımni ret ve açık ret arasındaki süre farkı karşılaştırılıyor."),
    3: ("comparison", "İki farklı suç ve soruşturma usulleri karşılaştırılıyor."),
    4: ("comparison", "Kanun değişikliği öncesi ve sonrası karşılaştırılıyor."),
    5: ("comparison", "İYUK 10 ve 11. maddelerin uygulama alanları karşılaştırılıyor."),
    6: ("comparison", "Somut ve soyut tehlike suçu ayrımı isteniyor."),
    7: ("comparison", "Avukatların çekinme hakkı diğer mesleklerle karşılaştırılıyor."),
    8: ("comparison", "İki hukuka aykırılık türünün sonuçları karşılaştırılıyor."),
    9: ("comparison", "Suçun basit ve nitelikli hallerinin uzlaştırma bakımından farkı soruluyor."),
    10: ("comparison", "Geçerli ve haklı fesih nedenlerinin süre farkı soruluyor."),
    11: ("case_application", "Somut hükümlü durumuna seçenek yaptırım kurallarının uygulanması soruluyor."),
    12: ("penalty_sanction", "Belirli suçun cezası doğrudan soruluyor."),
    13: ("penalty_sanction", "Ceza miktarının nasıl belirleneceği soruluyor."),
    14: ("penalty_sanction", "Suçun işlenişi ve cezası soruluyor; birincil etiket yaptırım."),
    15: ("case_application", "Somut çocuk alıkoyma olayının suç niteliği ve cezası soruluyor."),
    16: ("penalty_sanction", "Belirli eylemin cezası soruluyor."),
    17: ("penalty_sanction", "Örgüt üyeliğinin cezası soruluyor."),
    18: ("case_application", "Somut olayda iki suç hükmünün birlikte uygulanması soruluyor."),
    19: ("penalty_sanction", "Fotoğraf paylaşımının ceza yaptırımı soruluyor."),
    20: ("procedure_deadline", "Esas görev temyiz yoluna başvurulabilirliği belirlemek."),
    21: ("procedure_deadline", "Zamanaşımı süresi ve başlangıcı soruluyor."),
    22: ("case_application", "Somut feragat ve ödeme olayının delil değeri tartışılıyor."),
    23: ("legal_effect", "Affetmenin dava hakkına hukuki etkisi soruluyor."),
    24: ("procedure_deadline", "Ek savunma için süre verilmesi usulü soruluyor."),
    25: ("procedure_deadline", "Yetkili mahkeme ve itiraz süresi soruluyor."),
}

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 70:
    raise ValueError("70 kayıtlık inceleme dosyası bekleniyordu.")

expected_auto = {
    **{n: "comparison" for n in range(1, 11)},
    **{n: "penalty_sanction" for n in range(11, 21)},
    **{n: "procedure_deadline" for n in range(21, 26)},
}

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        if row["automatic_label"] != expected_auto[n]:
            raise ValueError(
                f"{n}. kaydın otomatik etiketi beklenenden farklı."
            )

        if row["correct_label"].strip():
            raise ValueError(
                f"{n}. kayıt zaten değerlendirilmiş."
            )

if not BACKUP.exists():
    shutil.copy2(PATH, BACKUP)

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        correct_label, reason = REVIEWS[n]

        row["label_correct"] = (
            "yes"
            if row["automatic_label"] == correct_label
            else "no"
        )
        row["correct_label"] = correct_label
        row["review_notes"] = (
            reason
            + " Sadece sorunun görev türü değerlendirildi; "
            + "cevabın hukuki doğruluğu incelenmedi."
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
    if row["correct_label"].strip()
]

pending = len(rows) - len(reviewed)

status = Counter(
    row["label_correct"] for row in reviewed
)

print("LEXITECH TR - GÖREV TÜRÜ KALİTE KAYDI")
print("=" * 55)
print("Toplam örnek:", len(rows))
print("Değerlendirilen:", len(reviewed))
print("Kalan:", pending)
print("Otomatik etiket doğru:", status["yes"])
print("Otomatik etiket değiştirildi:", status["no"])
print("Yedek:", BACKUP)
print("Güncellenen:", PATH)
print("Hukuki doğruluk kontrolü yapılmadı.")
print("Ana veri setleri değiştirilmedi.")

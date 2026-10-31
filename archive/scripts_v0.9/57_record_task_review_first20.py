import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_task_type_review_70_v0.9.csv"
)

BACKUP = PATH.with_name(
    "instruction_task_type_review_70_v0.9_backup.csv"
)

# Kayıt numarası: (önerilen doğru görev, gerekçe)
REVIEWS = {
    51: ("case_application", "Örgüt üyesinin somut hukuki sorumluluğu soruluyor."),
    52: ("legal_conditions", "Suçun unsurlarından birinin gerekli olup olmadığı soruluyor."),
    53: ("case_law_analysis", "Delilin değeri ve Yargıtay yaklaşımı analiz ediliyor."),
    54: ("legal_conditions", "Yoksulluk nafakasının koşulları soruluyor."),
    55: ("procedure_deadline", "Yargılamanın yenilenmesinde delil toplama usulü soruluyor."),
    56: ("legal_conditions", "Suçtan sorumluluk için gereken kastın yönü soruluyor."),
    57: ("case_law_analysis", "Yargıtay kararı ve hukuka aykırı delil yorumu soruluyor."),
    58: ("case_application", "Paylı eşyanın müsaderesinde kuralın uygulanması soruluyor."),
    59: ("case_application", "Önceki cezanın sonraki hukuki duruma etkisi soruluyor."),
    60: ("case_application", "Verilen somut olaya suç hükümlerinin uygulanması soruluyor."),
    61: ("procedure_deadline", "Tutukluluğun inceleme sıklığı ve usulü soruluyor."),
    62: ("procedure_deadline", "Şikayet süresi ve hak sahiplerine etkisi soruluyor."),
    63: ("case_law_analysis", "Belirli YHGK kararı ve ispat delilleri inceleniyor."),
    64: ("legal_effect", "Yeni kanunun ultra vires ilkesine etkisi soruluyor."),
    65: ("legal_conditions", "Boşanma sebebi için yeterlilik şartı soruluyor."),
    66: ("definition", "Fonksiyon gaspı kavramının anlamı soruluyor."),
    67: ("legal_conditions", "Miras payının hangi mirasçı sınıfına göre belirlendiği soruluyor."),
    68: ("case_application", "Somut e-posta olayına uygulanabilecek suçlar soruluyor."),
    69: ("legal_effect", "İptal kararının hukuki sonuçları soruluyor."),
    70: ("legal_conditions", "Sigortalı kapsamının istisnası soruluyor."),
}

with PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or len(rows) != 70:
    raise ValueError("70 satırlık inceleme dosyası bekleniyordu.")

found = {int(row["review_number"]) for row in rows}

if not set(REVIEWS).issubset(found):
    raise ValueError("İncelenecek kayıt numaraları bulunamadı.")

# Yanlış dosyayı güncelleme riskine karşı kontrol.
expected_labels = {
    **{i: "article_explanation" for i in range(51, 61)},
    **{i: "other" for i in range(61, 71)},
}

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        if row["automatic_label"] != expected_labels[n]:
            raise ValueError(f"{n}. kaydın otomatik etiketi değişmiş.")

        if row["correct_label"].strip():
            raise ValueError(f"{n}. kayıt önceden değerlendirilmiş.")

shutil.copy2(PATH, BACKUP)

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        label, reason = REVIEWS[n]
        row["label_correct"] = "no"
        row["correct_label"] = label
        row["review_notes"] = (
            reason + " Yalnızca görev türü incelendi; "
            "hukuki doğruluk doğrulanmadı."
        )

tmp = PATH.with_suffix(".csv.tmp")

with tmp.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(PATH)

counts = Counter(
    "reviewed" if row["correct_label"].strip() else "pending"
    for row in rows
)

new_labels = Counter(
    row["correct_label"]
    for row in rows
    if row["correct_label"].strip()
)

print("LEXITECH TR - GÖREV TÜRÜ MANUEL KAYDI")
print("=" * 55)
print("Toplam örnek:", len(rows))
print("Değerlendirilen:", counts["reviewed"])
print("Kalan:", counts["pending"])
print("Yedek:", BACKUP)
print("Güncellenen dosya:", PATH)

print("\nÖNERİLEN GÖREV DAĞILIMI (20 ÖRNEK)")
for label, count in new_labels.most_common():
    print(f"{label}: {count}")

print("\nHukuki cevap doğruluğu kontrol edilmedi.")
print("124.510 kayıtlık veri seti değiştirilmedi.")

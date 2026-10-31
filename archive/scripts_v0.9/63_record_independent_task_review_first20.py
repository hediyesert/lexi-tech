import csv
import shutil
from collections import Counter
from pathlib import Path

PATH = Path(
    "data/interim/instruction_task_independent_review_50_v0.9.csv"
)
BACKUP = PATH.with_name(
    "instruction_task_independent_review_50_before_first20_v0.9.csv"
)

REVIEWS = {
    1: ("comparison", "İki suçun farkı soruluyor."),
    2: ("case_application", "Somut ihale eyleminin suç niteliği soruluyor."),
    3: ("comparison", "İki usuli hakkın farkı soruluyor."),
    4: ("comparison", "Gönüllü vazgeçme ve etkin pişmanlık karşılaştırılıyor."),
    5: ("comparison", "İki infaz rejimi karşılaştırılıyor."),
    6: ("case_law_analysis", "Belirli Yargıtay kararının gerekçesi soruluyor."),
    7: ("case_law_analysis", "Yargıtay kararındaki düzeltme değerlendiriliyor."),
    8: ("case_law_analysis", "Belirli kararın kanun uygulamasına yaklaşımı soruluyor."),
    9: ("case_law_analysis", "Belirli Yargıtay kararının değerlendirmesi soruluyor."),
    10: ("case_law_analysis", "Doktrin ve Yargıtay yaklaşımı analiz ediliyor."),
    11: ("case_application", "Somut senet kullanımına suç hükmü uygulanıyor."),
    12: ("case_law_analysis", "Belirli Yargıtay kararındaki indirim gerekçesi sorgulanıyor."),
    13: ("case_application", "Sanığın somut hukuki durumunun sonucu soruluyor."),
    14: ("case_application", "Somut olaya içtima kuralları uygulanıyor."),
    15: ("case_application", "Somut telefon numarası paylaşımının suçu soruluyor."),
    16: ("comparison", "İki düzenlemenin hukuki sonuçları karşılaştırılıyor."),
    17: ("legal_effect", "Orantılılık ihlalinin hukuki sonucu soruluyor."),
    18: ("legal_effect", "Tutanak eksikliğinin delil değerine etkisi soruluyor."),
    19: ("legal_effect", "Erteleme süresindeki yeni fiilin sonuçları soruluyor."),
    20: ("legal_effect", "Ceza zamanaşımının hak yoksunluklarına etkisi soruluyor."),
}

EXPECTED = {
    **{n: "comparison" for n in range(1, 6)},
    **{n: "case_law_analysis" for n in range(6, 11)},
    **{n: "case_application" for n in range(11, 16)},
    **{n: "legal_effect" for n in range(16, 21)},
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

numbers = [int(row["review_number"]) for row in rows]

if sorted(numbers) != list(range(1, 51)):
    raise ValueError("Kayıt numaraları beklenenden farklı.")

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        if row["predicted_label"] != EXPECTED[n]:
            raise ValueError(f"{n}. kaydın otomatik etiketi değişmiş.")

        if row["reviewer_label"].strip():
            raise ValueError(f"{n}. kayıt zaten değerlendirilmiş.")

shutil.copy2(PATH, BACKUP)

for row in rows:
    n = int(row["review_number"])

    if n in REVIEWS:
        proposed_label, reason = REVIEWS[n]
        row["reviewer_label"] = proposed_label
        row["review_status"] = "assistant_proposed"
        row["reviewer_notes"] = (
            reason
            + " Asistanın görev etiketi önerisidir; "
            + "bağımsız uzman onayı veya hukuki doğruluk denetimi değildir."
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

agreement = Counter(
    "same" if row["predicted_label"] == row["reviewer_label"]
    else "different"
    for row in reviewed
)

print("LEXITECH TR - YENİ TEST İLK 20 KAYIT")
print("=" * 55)
print("Toplam test sorusu:", len(rows))
print("Asistan etiketi önerilen:", len(reviewed))
print("Kalan:", len(rows) - len(reviewed))
print("Otomatik etiketle uyumlu:", agreement["same"])
print("Değişiklik önerilen:", agreement["different"])
print("Yedek:", BACKUP)
print("Güncellenen dosya:", PATH)
print("Bağımsız insan uzman onayı: 0")
print("Ana veri setleri değiştirilmedi.")

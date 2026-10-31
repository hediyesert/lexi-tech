import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path("reports/statistics")
DATA = Path("data/interim")

DIST_PATH = BASE / "instruction_task_distribution_v0.9_2.json"
DEV_PATH = DATA / "instruction_task_type_review_70_v0.9.csv"
TEST_PATH = DATA / "instruction_task_independent_review_50_v0.9.csv"

JSON_OUT = BASE / "instruction_task_quality_v0.9_2.json"
MD_OUT = BASE / "instruction_task_quality_v0.9_2.md"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

distribution = json.loads(
    DIST_PATH.read_text(encoding="utf-8")
)
development = read_csv(DEV_PATH)
test = read_csv(TEST_PATH)

if len(development) != 70 or len(test) != 50:
    raise ValueError("70 geliştirme ve 50 test kaydı bekleniyordu.")

if distribution["total"] != 124510:
    raise ValueError("Görev dağılımı toplamı beklenenden farklı.")

if any(not r["correct_label"].strip() for r in development):
    raise ValueError("Geliştirme örneklerinde boş etiket var.")

if any(not r["reviewer_label"].strip() for r in test):
    raise ValueError("Test örneklerinde boş etiket var.")

if any(r["review_status"] != "assistant_proposed" for r in test):
    raise ValueError("Beklenmeyen değerlendirme durumu bulundu.")

dev_same = sum(
    r["automatic_label"] == r["correct_label"]
    for r in development
)

test_same = sum(
    r["predicted_label"] == r["reviewer_label"]
    for r in test
)

if dev_same != 30 or test_same != 37:
    raise ValueError(
        "Önceden kaydedilen değerlendirme sayıları uyuşmuyor."
    )

by_category = defaultdict(lambda: Counter())
mismatches = []

for row in test:
    predicted = row["predicted_label"]
    proposed = row["reviewer_label"]
    by_category[predicted]["total"] += 1

    if predicted == proposed:
        by_category[predicted]["same"] += 1
    else:
        by_category[predicted]["different"] += 1
        mismatches.append({
            "review_number": int(row["review_number"]),
            "predicted_label": predicted,
            "assistant_proposed_label": proposed,
        })

category_summary = []

for label, stats in sorted(by_category.items()):
    count = stats["total"]

    category_summary.append({
        "predicted_label": label,
        "sample_count": count,
        "agreement_count": stats["same"],
        "disagreement_count": stats["different"],
        "sample_agreement_percent": round(
            100 * stats["same"] / count, 2
        ),
    })

report = {
    "project": "LexiTech TR",
    "version": "v0.9.2",
    "question": 15,
    "classification_status": "experimental",
    "dataset_records": distribution["total"],
    "task_distribution": distribution["distribution"],
    "development_sample": {
        "size": 70,
        "agreement": dev_same,
        "disagreement": 70 - dev_same,
        "used_for_rule_development": True,
    },
    "held_out_from_development_sample": {
        "size": 50,
        "agreement": test_same,
        "disagreement": 50 - test_same,
        "unweighted_agreement_percent": round(
            100 * test_same / 50, 2
        ),
        "annotation_source": "assistant_proposed",
        "independent_human_verified": False,
        "balanced_by_predicted_category": True,
    },
    "by_predicted_category": category_summary,
    "disagreements": mismatches,
    "limitations": [
        "Test soruları geliştirmedeki 70 sorudan ayrıdır.",
        "Test etiketleri asistan tarafından önerilmiştir.",
        "Bağımsız insan veya hukukçu doğrulaması yoktur.",
        "Her tahmin kategorisinden 5 soru seçilmiştir.",
        "Yuzde 74 tum veri setinin dogruluk orani degildir.",
        "Other kategorisindeki kayıt sayısı yüksektir.",
        "Birincil görev etiketi çok görevli soruları basitleştirir.",
        "Hukuki cevap doğruluğu bu çalışmada ölçülmemiştir."
    ]
}

lines = [
    "# LexiTech TR — Görev Türü Kalite Raporu v0.9.2",
    "",
    "## Kapsam",
    "",
    "- Danışman sorusu: **15**",
    "- Veri seti: **124.510 soru-cevap kaydı**",
    "- Yöntem: kural ve anahtar kelime tabanlı sınıflandırma",
    "- Durum: **Deneysel; nihai olarak onaylanmadı**",
    "",
    "## Değerlendirme sonuçları",
    "",
    "| Ölçüm | Sonuç |",
    "|---|---:|",
    f"| Geliştirme örnekleri | {len(development)} |",
    f"| Geliştirme uyumu | {dev_same}/{len(development)} |",
    f"| Ayrı tutulan test örnekleri | {len(test)} |",
    f"| Test uyumu | {test_same}/{len(test)} (%74,00) |",
    "| Bağımsız insan uzman onayı | 0 |",
    "",
    "## Tahmin kategorilerine göre test sonucu",
    "",
    "| Tahmin kategorisi | Örnek | Uyumlu | Farklı |",
    "|---|---:|---:|---:|",
]

for item in category_summary:
    lines.append(
        f"| {item['predicted_label']} "
        f"| {item['sample_count']} "
        f"| {item['agreement_count']} "
        f"| {item['disagreement_count']} |"
    )

lines += [
    "",
    "## Veri seti görev dağılımı",
    "",
    "| Görev türü | Kayıt | Yüzde |",
    "|---|---:|---:|",
]

for label, values in distribution["distribution"].items():
    lines.append(
        f"| {label} | {values['count']} "
        f"| %{values['percent']:.2f} |"
    )

lines += [
    "",
    "## Sınırlılıklar ve sonraki işler",
    "",
    "- **%74**, eşit kategorili 50 örnekte asistan "
    "etiketleriyle uyumdur; tüm veri setinin doğruluğu değildir.",
    "- Test örnekleri geliştirme örneklerinden ayrı tutulmuştur "
    "ancak bağımsız insan tarafından etiketlenmemiştir.",
    "- `other` oranı yüksek olduğundan sınıflandırıcı "
    "iyileştirme ve ek analiz gerektirir.",
    "- Görev sınıflandırması, hukuki cevapların "
    "doğruluğunu veya kullanım izinlerini kanıtlamaz.",
    "- Bağımsız insan incelemesi ve dağılıma uygun "
    "rastgele örneklem değerlendirmesi gereklidir.",
    "",
    "## Sonuç",
    "",
    "Danışmanın 15. sorusu için sayısal dağılım ve "
    "ön kalite analizi hazırlanmıştır. Bağımsız "
    "doğrulama tamamlanmadığı için nihai kabul verilmemiştir.",
    "",
]

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit(
        "Çıktı dosyalarından biri zaten mevcut; "
        "üzerine yazılmadı."
    )

BASE.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
MD_OUT.write_text("\n".join(lines), encoding="utf-8")

print("LEXITECH TR - GÖREV TÜRÜ KALİTE RAPORU")
print("=" * 55)
print("Veri seti:", distribution["total"])
print("Geliştirme örnekleri:", len(development))
print("Ayrı test örnekleri:", len(test))
print("Test etiketi uyumu:", f"{test_same}/{len(test)}")
print("Değişiklik önerisi:", len(mismatches))

print("\nKATEGORİ BAZLI TEST SONUÇLARI")
for item in category_summary:
    print(
        f"{item['predicted_label']:<25} "
        f"{item['agreement_count']}/{item['sample_count']}"
    )

print("\nJSON raporu:", JSON_OUT)
print("Markdown raporu:", MD_OUT)
print("Bağımsız uzman onayı: 0")
print("Ana veri setleri değiştirilmedi.")

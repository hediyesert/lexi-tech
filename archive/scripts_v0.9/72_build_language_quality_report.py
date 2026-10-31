import csv
import json
from collections import Counter
from pathlib import Path

STATS = Path("reports/statistics")

FULL = STATS / "instruction_language_full_v0.9.json"
PILOT = STATS / "language_distribution_pilot_v0.9.json"
REVIEW = Path(
    "data/interim/instruction_language_manual_review_123_v0.9.csv"
)

JSON_OUT = STATS / "language_quality_report_v0.9.json"
MD_OUT = STATS / "language_quality_report_v0.9.md"

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit(
        "Rapor dosyası zaten mevcut; üzerine yazılmadı."
    )

full = json.loads(FULL.read_text(encoding="utf-8"))
pilot = json.loads(PILOT.read_text(encoding="utf-8"))

with REVIEW.open(encoding="utf-8-sig", newline="") as f:
    reviews = list(csv.DictReader(f))

total = full["total_records"]

if total != 124510:
    raise ValueError("Toplam QA sayısı uyuşmuyor.")

if len(reviews) != 123:
    raise ValueError("123 inceleme satırı bekleniyordu.")

if any(
    row["review_status"] != "assistant_preliminary"
    for row in reviews
):
    raise ValueError("Tamamlanmamış inceleme kaydı var.")

flags = full["flagged_records"]

expected = set()

for item in flags:
    for field in ("question", "answer"):
        if item[f"{field}_category"] != "tr":
            expected.add((item["id"], field))

actual = [
    (row["record_id"], row["text_field"])
    for row in reviews
]

if len(actual) != len(set(actual)):
    raise ValueError("Tekrarlı inceleme satırı bulundu.")

if set(actual) != expected:
    raise ValueError(
        "Manuel inceleme tablosu otomatik işaretlerle uyuşmuyor."
    )

assessment = Counter(
    row["assistant_language_assessment"]
    for row in reviews
)

if assessment["tr"] != 122:
    raise ValueError("122 Türkçe ön değerlendirme bekleniyordu.")

if assessment["not_assessable"] != 1:
    raise ValueError("1 sınıflandırılamayan kayıt bekleniyordu.")

quality = [
    row for row in reviews
    if row["question_quality_flag"].strip()
]

if len(quality) != 2:
    raise ValueError("2 soru kalitesi uyarısı bekleniyordu.")

by_field = {}

for field in ("question", "answer"):
    original = full[f"{field}_categories"]

    approved_by_assistant = sum(
        row["text_field"] == field
        and row["assistant_language_assessment"] == "tr"
        for row in reviews
    )

    unresolved = sum(
        row["text_field"] == field
        and row["assistant_language_assessment"] != "tr"
        for row in reviews
    )

    automatic_tr = original.get("tr", 0)
    combined_tr = automatic_tr + approved_by_assistant

    if combined_tr + unresolved != total:
        raise ValueError(
            f"{field}: sayılar toplamla uyuşmuyor."
        )

    by_field[field] = {
        "automatically_detected_tr": automatic_tr,
        "assistant_assessed_tr": approved_by_assistant,
        "combined_tr_count": combined_tr,
        "combined_tr_percent": round(
            100 * combined_tr / total, 4
        ),
        "still_unclassified": unresolved,
        "automatic_categories": original,
    }

domain = pilot["domain"]

if domain["documents"] != 12:
    raise ValueError("12 kanun bekleniyordu.")

if domain["sampled_passages"] != 60:
    raise ValueError("60 Domain metin parçası bekleniyordu.")

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "advisor_question": 10,
    "status": "automated_full_scan_and_assistant_preliminary_review",
    "instruction_total_records": total,
    "instruction": by_field,
    "flagged_texts": len(reviews),
    "assistant_preliminary_tr": assessment["tr"],
    "not_assessable": assessment["not_assessable"],
    "pending_assistant_review": 0,
    "independent_human_review_count": 0,
    "question_quality_flags": [
        {
            "review_number": int(row["review_number"]),
            "record_id": row["record_id"],
            "flag": row["question_quality_flag"],
        }
        for row in quality
    ],
    "domain_sample": {
        "documents": domain["documents"],
        "passages": domain["sampled_passages"],
        "categories": domain["categories"],
    },
    "limitations": [
        "Dil tespiti langdetect 1.0.9 ile yapıldı.",
        "Otomatik dil tespiti ve olasılıkları hatasız değildir.",
        "123 işaretli metin asistan tarafından ön değerlendirildi.",
        "Bağımsız insan uzman onayı bulunmuyor.",
        "Karma dil içeriği her zaman yakalanamayabilir.",
        "Domain sonucu bütün metnin değil 60 parçanın analizidir.",
        "İki soru kalitesi uyarısı henüz çözülmedi.",
        "Dil kontrolü hukuki doğruluğu veya kullanım hakkını kanıtlamaz."
    ]
}

STATS.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

lines = [
    "# LexiTech TR — Dil Kalitesi Raporu v0.9",
    "",
    "## Kapsam",
    "",
    "- Danışman sorusu: **10 — Dil dağılımı**",
    "- Instruction Dataset: **124.510 QA**",
    "- Domain Corpus: **12 kanundan 60 örnek metin parçası**",
    "- Yöntem: langdetect 1.0.9 ve asistan ön değerlendirmesi",
    "",
    "## Instruction Dataset sonuçları",
    "",
    "| Ölçüm | Soru | Cevap |",
    "|---|---:|---:|",
    (
        "| Otomatik Türkçe | "
        f"{by_field['question']['automatically_detected_tr']:,} | "
        f"{by_field['answer']['automatically_detected_tr']:,} |"
    ),
    (
        "| Asistan tarafından Türkçe görülen ek metin | "
        f"{by_field['question']['assistant_assessed_tr']} | "
        f"{by_field['answer']['assistant_assessed_tr']} |"
    ),
    (
        "| Birleşik Türkçe değerlendirmesi | "
        f"{by_field['question']['combined_tr_count']:,} | "
        f"{by_field['answer']['combined_tr_count']:,} |"
    ),
    (
        "| Dil durumu sınıflandırılamayan | "
        f"{by_field['question']['still_unclassified']} | "
        f"{by_field['answer']['still_unclassified']} |"
    ),
    "",
    "Birleşik değerlendirme, otomatik tespit ile "
    "asistanın ön incelemesini birlikte gösterir; "
    "**bağımsız insan tarafından doğrulanmış oran değildir.**",
    "",
    "## Domain Corpus",
    "",
    f"- Belge: **{domain['documents']}**",
    f"- İncelenen metin parçası: **{domain['sampled_passages']}**",
    f"- Otomatik Türkçe tespit edilen: "
    f"**{domain['categories'].get('tr', 0)}**",
    "",
    "## İşaretli kayıt incelemesi",
    "",
    "- Asistanın ön değerlendirdiği metin: **123**",
    "- Türkçe görünen metin: **122**",
    "- Dil açısından sınıflandırılamayan: **1**",
    "- Ayrı soru kalitesi uyarısı: **2**",
    "- Bağımsız insan uzman onayı: **0**",
    "",
    "### Soru kalitesi uyarıları",
    "",
]

for row in quality:
    lines.append(
        f"- İnceleme #{row['review_number']}: "
        f"`{row['question_quality_flag']}`"
    )

lines += [
    "",
    "## Sınırlılıklar",
    "",
]

for limitation in report["limitations"]:
    lines.append(f"- {limitation}")

lines += [
    "",
    "## Sonuç",
    "",
    "Dil dağılımı için tam otomatik Instruction taraması "
    "ve işaretli metinlerin asistan ön incelemesi tamamlandı. "
    "Bağımsız doğrulama ve iki soru kalitesi sorununun "
    "çözümü sonraki aşamalar için açık kaldı.",
    "",
]

MD_OUT.write_text("\n".join(lines), encoding="utf-8")

print("LEXITECH TR - DİL KALİTE RAPORU")
print("=" * 60)

print("Toplam Instruction QA:", total)

for field, label in (
    ("question", "SORULAR"),
    ("answer", "CEVAPLAR"),
):
    result = by_field[field]
    print(f"\n{label}")
    print("Otomatik Türkçe:", result["automatically_detected_tr"])
    print("Ek Türkçe ön değerlendirmesi:", result["assistant_assessed_tr"])
    print("Birleşik Türkçe:", result["combined_tr_count"])
    print("Sınıflandırılamayan:", result["still_unclassified"])

print("\nDOMAIN CORPUS")
print("Kanun:", domain["documents"])
print("İncelenen parça:", domain["sampled_passages"])
print("Türkçe tespit edilen:", domain["categories"].get("tr", 0))

print("\nSoru kalitesi uyarısı:", len(quality))
print("Bağımsız insan onayı: 0")
print("\nJSON:", JSON_OUT)
print("Markdown:", MD_OUT)
print("Ana veri setleri değiştirilmedi.")

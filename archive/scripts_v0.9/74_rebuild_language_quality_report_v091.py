import csv
import json
from collections import Counter
from pathlib import Path

STATS = Path("reports/statistics")
REVIEW = Path(
    "data/interim/instruction_language_manual_review_123_v0.9.csv"
)

FULL = STATS / "instruction_language_full_v0.9.json"
PILOT = STATS / "language_distribution_pilot_v0.9.json"

JSON_OUT = STATS / "language_quality_report_v0.9.1.json"
MD_OUT = STATS / "language_quality_report_v0.9.1.md"

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit(
        "Yeni rapor zaten mevcut. Üzerine yazılmadı."
    )

full = json.loads(FULL.read_text(encoding="utf-8"))
pilot = json.loads(PILOT.read_text(encoding="utf-8"))

with REVIEW.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

total = full["total_records"]

if total != 124510 or len(rows) != 123:
    raise ValueError("Kayıt sayıları uyuşmuyor.")

if any(
    row["review_status"] != "assistant_preliminary"
    for row in rows
):
    raise ValueError("Tamamlanmamış ön değerlendirme var.")

if any(
    row["text_field"] not in ("question", "answer")
    for row in rows
):
    raise ValueError("Bilinmeyen metin alanı var.")

# İnceleme tablosunun otomatik taramada işaretlenen
# kayıtlarla birebir eşleştiğini doğrula.
expected = set()

for item in full["flagged_records"]:
    for field in ("question", "answer"):
        if item[f"{field}_category"] != "tr":
            expected.add((item["id"], field))

actual = [
    (row["record_id"], row["text_field"])
    for row in rows
]

if len(set(actual)) != len(actual):
    raise ValueError("Tekrarlı inceleme kaydı var.")

if set(actual) != expected:
    raise ValueError(
        "Otomatik tarama ve inceleme tablosu uyuşmuyor."
    )

assessments = Counter(
    row["assistant_language_assessment"]
    for row in rows
)

if assessments["tr"] != 122:
    raise ValueError("122 Türkçe ön değerlendirme bekleniyor.")

if assessments["not_assessable"] != 1:
    raise ValueError(
        "1 sınıflandırılamayan metin bekleniyor."
    )

question_flags = [
    row for row in rows
    if row["question_quality_flag"].strip()
]

answer_flags = [
    row for row in rows
    if row["answer_quality_flag"].strip()
]

if (
    len(question_flags) != 1
    or len(answer_flags) != 1
    or int(question_flags[0]["review_number"]) != 120
    or int(answer_flags[0]["review_number"]) != 36
):
    raise ValueError(
        "Kalite uyarıları beklenen kayıtlarda değil."
    )

results = {}

for field in ("question", "answer"):
    auto = full[f"{field}_categories"]
    auto_tr = auto.get("tr", 0)

    extra_tr = sum(
        row["text_field"] == field
        and row["assistant_language_assessment"] == "tr"
        for row in rows
    )

    unresolved = sum(
        row["text_field"] == field
        and row["assistant_language_assessment"] != "tr"
        for row in rows
    )

    combined = auto_tr + extra_tr

    if combined + unresolved != total:
        raise ValueError(
            f"{field} için toplam sayılar uyuşmuyor."
        )

    results[field] = {
        "automatic_tr": auto_tr,
        "assistant_preliminary_tr": extra_tr,
        "combined_tr": combined,
        "combined_tr_percent": round(
            100 * combined / total, 4
        ),
        "unresolved": unresolved,
        "automatic_categories": auto
    }

domain = pilot["domain"]

if (
    domain["documents"] != 12
    or domain["sampled_passages"] != 60
):
    raise ValueError("Domain örneklem sayıları uyuşmuyor.")

report = {
    "project": "LexiTech TR",
    "version": "v0.9.1",
    "supersedes": "language_quality_report_v0.9",
    "advisor_question": 10,
    "status": "automated_scan_plus_assistant_preliminary_review",
    "instruction_total_qa": total,
    "instruction": results,
    "flagged_texts_reviewed": len(rows),
    "assistant_preliminary_tr": assessments["tr"],
    "language_not_assessable": assessments["not_assessable"],
    "independent_human_approved": 0,
    "question_quality_issues": [
        {
            "review_number": int(row["review_number"]),
            "flag": row["question_quality_flag"],
            "record_id": row["record_id"],
        }
        for row in question_flags
    ],
    "answer_quality_issues": [
        {
            "review_number": int(row["review_number"]),
            "flag": row["answer_quality_flag"],
            "record_id": row["record_id"],
        }
        for row in answer_flags
    ],
    "domain_sample": {
        "documents": domain["documents"],
        "passages": domain["sampled_passages"],
        "automatic_categories": domain["categories"],
    },
    "limitations": [
        "Otomatik dil tespiti hatasız değildir.",
        "Asistan değerlendirmesi bağımsız uzman onayı değildir.",
        "Bir cevap dil açısından sınıflandırılamadı.",
        "Domain sonucu 60 örnek metin parçasına dayanır.",
        "Karma dil içeriği her zaman tespit edilemeyebilir.",
        "Soru ve cevap kalitesi sorunları henüz giderilmedi.",
        "Dil analizi hukuki doğruluğu ve lisansı kanıtlamaz."
    ]
}

lines = [
    "# LexiTech TR — Dil Kalitesi Raporu v0.9.1",
    "",
    "**Danışman sorusu:** 10 — Dil dağılımı",
    "",
    "Bu sürüm v0.9 raporundaki kalite uyarısı "
    "alanlarını düzeltir.",
    "",
    "## Instruction Dataset",
    "",
    "| Ölçüm | Soru | Cevap |",
    "|---|---:|---:|",
    (
        f"| Otomatik Türkçe | "
        f"{results['question']['automatic_tr']:,} | "
        f"{results['answer']['automatic_tr']:,} |"
    ),
    (
        f"| Asistanın ek Türkçe ön değerlendirmesi | "
        f"{results['question']['assistant_preliminary_tr']} | "
        f"{results['answer']['assistant_preliminary_tr']} |"
    ),
    (
        f"| Birleşik Türkçe değerlendirmesi | "
        f"{results['question']['combined_tr']:,} | "
        f"{results['answer']['combined_tr']:,} |"
    ),
    (
        f"| Sınıflandırılamayan | "
        f"{results['question']['unresolved']} | "
        f"{results['answer']['unresolved']} |"
    ),
    "",
    "**Önemli:** Birleşik sonuç bağımsız insan "
    "tarafından doğrulanmış dil oranı değildir.",
    "",
    "## Domain Corpus",
    "",
    "- Kanun sayısı: 12",
    "- İncelenen metin parçası: 60",
    f"- Otomatik Türkçe: "
    f"{domain['categories'].get('tr', 0)}/60",
    "",
    "## Soru ve cevap kalitesi sorunları",
    "",
    "- İnceleme 36: **Cevap** — "
    "`citation_only_answer`",
    "- İnceleme 120: **Soru** — "
    "`incomplete_question_fragment`",
    "",
    "Bu sorunlar dil hatasıyla aynı şey değildir.",
    "",
    "## Sınırlılıklar",
    "",
]

lines.extend(
    f"- {item}" for item in report["limitations"]
)

lines += [
    "",
    "## Sonuç",
    "",
    "Tam Instruction otomatik taraması ve işaretlenen "
    "123 metnin asistan ön incelemesi tamamlandı. "
    "Bağımsız doğrulama ve veri kalitesi düzeltmeleri "
    "henüz tamamlanmadı.",
    "",
]

STATS.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

MD_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("LEXITECH TR - DUZELTILMIS DIL RAPORU v0.9.1")
print("=" * 60)

for field, label in (
    ("question", "SORULAR"),
    ("answer", "CEVAPLAR")
):
    result = results[field]
    print(f"\n{label}")
    print("Otomatik Turkce:", result["automatic_tr"])
    print("Ek Turkce on degerlendirme:",
          result["assistant_preliminary_tr"])
    print("Birlesik Turkce:", result["combined_tr"])
    print("Siniflandirilamayan:", result["unresolved"])

print("\nSoru kalitesi uyarisi:", len(question_flags))
print("Cevap kalitesi uyarisi:", len(answer_flags))
print("Bagimsiz uzman onayi: 0")

print("\nJSON raporu:", JSON_OUT)
print("Markdown raporu:", MD_OUT)
print("Ana veri setleri degistirilmedi.")

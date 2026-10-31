import csv
import json
import re
from collections import Counter
from pathlib import Path

DATA = Path("data/interim/instruction_leakage_clean_v0.9")
REVIEW = Path("data/interim/instruction_task_type_review_70_v0.9.csv")
OLD = Path("reports/statistics/instruction_task_distribution_v0.9_1.json")
OUTPUT = Path("reports/statistics/instruction_task_distribution_v0.9_2.json")

def matches(pattern, text):
    return bool(re.search(pattern, text, re.IGNORECASE))

def classify(question):
    q = " ".join(question.split())

    comparison = (
        r"\bkarşılaştır\w*"
        r"|\bfark(?:ı|lar|ları|lılıkları)?\b"
        r"|\bfarklılık\w*"
        r"|\barasında\s+ne\s+fark"
        r"|\böncesi\s+ve\s+sonrası"
        r"|\bsomut\s+tehlike\s+suçu.*soyut\s+tehlike"
    )

    case_law_source = (
        r"\byargıtay\b|\bdanıştay\b|\byhgk\b"
        r"|\bceza\s+genel\s+kurulu\b"
        r"|\biçtihad\w*"
    )

    case_law_analysis = (
        r"\byaklaşım\w*|\bgörüş\w*"
        r"|\bnasıl\s+yorumlan\w*"
        r"|\bnasıl\s+gerekçelendir\w*"
        r"|\bhangi\s+deliller\b"
        r"|\bkararında\s+nasıl\b"
        r"|\bkararındaki\b"
        r"|\bhukuki\s+nitelendirmesi\b"
        r"|\bkararını\s+analiz\b"
    )

    numbered_decision = (
        r"\b\d{4}/\d+\s*(?:E\.?|K\.?)"
        r"|\bE\s*:\s*\d{4}/\d+"
    )

    case_context = (
        r"\bsomut\s+olay\b"
        r"|\bbir\s+sanık\b|\bbir\s+sanığın\b"
        r"|\bbir\s+hükümlü\b|\bbir\s+hükümlünün\b"
        r"|\bbir\s+mükellef\b"
        r"|\bbir\s+polis\s+memuru\b"
        r"|\bbir\s+bekçi\b|\bbir\s+bekçinin\b"
        r"|\bbir\s+kişi\b|\bbir\s+kişinin\b"
        r"|\bbir\s+kadın\b|\bbir\s+annenin\b"
        r"|\bbu\s+olayda\b|\bbu\s+durumda\b"
    )

    application_action = (
        r"\buygulan\w*|\boluştur\w*"
        r"|\bsorumlu\s+tutul\w*"
        r"|\bkarar\s+verilebilir\s+mi\b"
        r"|\bengel\s+teşkil\b"
        r"|\bhukuki\s+nitelendir\w*"
        r"|\bgündeme\s+gelir\b"
        r"|\byararlanabilir\s+mi\b"
        r"|\bdelil\s+değeri\b"
        r"|\bceza\s+verilebilir\s+mi\b"
    )

    legal_effect = (
        r"\bhukuki\s+sonuç\w*"
        r"|\bsonuçları\s+nelerdir"
        r"|\bdava\s+hakkına\s+etkisi"
        r"|\bortadan\s+kaldırmış\s+mıdır"
        r"|\bnasıl\s+etkiler\b"
    )

    penalty = (
        r"\bcezası\s+nedir\b"
        r"|\bcezası\s+ne\s+kadar\b"
        r"|\bkaç\s+ceza\s+verilir\b"
        r"|\bne\s+kadar\s+ceza\b"
        r"|\bceza(?:sı|nın)\s+miktarı\b"
        r"|\bcezada\s+artırım\b"
        r"|\bcezasında\s+artırım\b"
        r"|\bcezası\s+nasıl\s+hesaplanır\b"
    )

    procedure = (
        r"\bzamanaşımı\b"
        r"|\bkaç\s+gün\b|\bne\s+sıklıkla\b"
        r"|\bne\s+kadar\s+sürede\b"
        r"|\bsüre\s+verilir\s+mi\b"
        r"|\bsüresi\s+ne\s+kadar\b"
        r"|\bne\s+zaman\s+(?:başlar|sona\s+erer|açabilir)"
        r"|\btemyiz\b|\bistinaf\b"
        r"|\bbaşvur\w*|\bitiraz\b"
        r"|\busul\w*|\bdava\s+aç\w*"
        r"|\bnasıl\s+talep\b"
        r"|\byetkili\s+mahkeme\b"
        r"|\bnasıl\s+bir\s+yol\s+izler\b"
    )

    conditions = (
        r"\bşart\w*|\bkoşul\w*"
        r"|\bhangi\s+hallerde\b"
        r"|\bhangi\s+durumlarda\b"
        r"|\byeterli\s+midir\b"
        r"|\bbir\s+unsur\s+mudur\b"
        r"|\bgerekir\s+mi\b"
        r"|\bistisnalar\w*"
        r"|\byararlanabilir\s+mi\b"
        r"|\bkim(?:ler)?\s+olabilir\b"
        r"|\bhangi\s+suçları\b"
    )

    definition = (
        r"\btanımı\s+nedir\b"
        r"|\bne\s+demektir\b"
        r"|\bne\s+anlama\s+gelir\b"
        r"|\bnedir\b"
        r"|\bkavramını\s+açıklayınız\b"
    )

    article = (
        r"\bmaddeyi\s+açıklayınız\b"
        r"|\bmaddenin\s+içeriğini\s+açıklayınız\b"
        r"|\bmadde\s+neyi\s+düzenler\b"
        r"|\bmaddesi\s+neyi\s+düzenler\b"
    )

    # Öncelik: sorunun asıl istediği görev.
    if matches(comparison, q):
        return "comparison"

    if matches(case_law_source, q) and (
        matches(case_law_analysis, q)
        or (
            matches(numbered_decision, q)
            and matches(r"\bkarar\w*", q)
        )
    ):
        return "case_law_analysis"

    if matches(case_context, q) and matches(application_action, q):
        return "case_application"

    if matches(legal_effect, q):
        return "legal_effect"

    if matches(penalty, q):
        return "penalty_sanction"

    if matches(procedure, q):
        return "procedure_deadline"

    if matches(conditions, q):
        return "legal_conditions"

    if matches(definition, q):
        return "definition"

    if matches(article, q):
        return "article_explanation"

    return "other"


counts = Counter()
by_split = {}
total = 0

for split in ("train", "validation", "test"):
    split_counts = Counter()

    with (DATA / f"{split}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            question = record["messages"][0]["content"]
            label = classify(question)

            counts[label] += 1
            split_counts[label] += 1
            total += 1

    by_split[split] = dict(split_counts)

if total != 124510:
    raise ValueError(f"Beklenen 124510, bulunan {total}")

with REVIEW.open(encoding="utf-8-sig", newline="") as f:
    reviews = list(csv.DictReader(f))

if len(reviews) != 70 or any(
    not row["correct_label"].strip() for row in reviews
):
    raise ValueError("70 tamamlanmış görev etiketi bekleniyordu.")

correct = sum(
    classify(row["question"]) == row["correct_label"]
    for row in reviews
)

old = json.loads(OLD.read_text(encoding="utf-8"))

report = {
    "version": "v0.9.2",
    "status": "development_candidate_not_independently_validated",
    "total": total,
    "distribution": {
        label: {
            "count": count,
            "percent": round(count * 100 / total, 2)
        }
        for label, count in counts.most_common()
    },
    "by_split": by_split,
    "development_review": {
        "sample_size": 70,
        "matches_assistant_proposed_labels": correct,
        "mismatches": 70 - correct,
        "agreement_percent": round(correct * 100 / 70, 2)
    },
    "limitations": [
        "Anahtar kelime ve kural tabanli deneysel sınıflandırıcı.",
        "70 örnek geliştirme sürecinde kullanıldı.",
        "70 örnekteki uyum bağımsız test başarısı değildir.",
        "Etiketler bağımsız insan veya hukuk uzmanı onaylı değildir.",
        "Hukuki cevap doğruluğu bu çalışmada değerlendirilmedi.",
        "Other kategorisi belirsiz veya yakalanamayan görevleri içerir."
    ]
}

if OUTPUT.exists():
    raise SystemExit(
        f"Çıktı mevcut; üzerine yazılmadı: {OUTPUT}"
    )

OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("LEXITECH TR - GÖREV SINIFLANDIRICISI v0.9.2")
print("=" * 60)
print("Toplam QA:", total)

print("\nGÖREV DAĞILIMI")
for label, count in counts.most_common():
    print(f"{label:<25} {count:>7,} %{count / total * 100:.2f}")

print("\nSÜRÜM KARŞILAŞTIRMASI")
print("v0.9.1 other:", old["distribution"]["other"]["count"])
print("v0.9.2 other:", counts["other"])
print(
    "70 geliştirme örneğinde uyum:",
    f"{correct}/70 (%{correct / 70 * 100:.2f})"
)

print("\nRapor:", OUTPUT)
print("Bağımsız test yapılmadı.")
print("Ana soru-cevap verileri değiştirilmedi.")

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path("data/interim/instruction_leakage_clean_v0.9")
REVIEW = Path(
    "data/interim/instruction_task_type_review_70_v0.9.csv"
)
OUTPUT = Path(
    "reports/statistics/instruction_task_distribution_v0.9_1.json"
)

RULES = {
    "comparison": (
        r"\bkarşılaştır\w*|\baralarındaki?\s+(?:temel\s+)?fark"
        r"|\bfark(?:ı|ları|lılıkları)\s+(?:nedir|nelerdir|var)"
        r"|\böncesi\s+ve\s+sonrası"
    ),
    "case_law_analysis": (
        r"\byargıtay\b|\bdanıştay\b|\byhgk\b"
        r"|\biçtihad\w*|\bceza genel kurulu\b"
    ),
    "case_application": (
        r"\bsomut olay\b|\bbir sanık\b|\bbir hükümlü\b"
        r"|\bbir mükellef\b|\bbir polis memuru\b"
        r"|\bbir kişinin\b|\bbir kişi\b"
        r"|\bbir kamu görevlisinin\b"
    ),
    "legal_effect": (
        r"\bhukuki sonuç\w*|\bsonuçları nelerdir"
        r"|\bdava hakkına etkisi\b"
        r"|\bortadan kaldırmış mıdır"
    ),
    "procedure_deadline": (
        r"\bzamanaşımı\b|\bkaç gün\b|\bne sıklıkla\b"
        r"|\bne kadar sürede\b|\bsüre(?:si|ler|de|yi)\b"
        r"|\btemyiz\b|\bistinaf\b|\bbaşvur\w*"
        r"|\bitiraz\b|\busul\b|\bdava aç\w*"
        r"|\bnasıl talep\b|\byetkili mahkeme\b"
    ),
    "legal_conditions": (
        r"\bşart(?:ı|ları)?\b|\bkoşul(?:u|ları)?\b"
        r"|\bhangi hallerde\b|\bhangi durumlarda\b"
        r"|\bhangi koşullarda\b|\bhangi şartlarda\b"
        r"|\byeterli midir\b|\bbir unsur mudur\b"
        r"|\bgerekir mi\b|\bistisnalar\w*\b"
    ),
    "penalty_sanction": (
        r"\bcezası nedir\b|\bcezası ne\b"
        r"|\bne kadar ceza\b|\bceza miktarı\b"
        r"|\bcezanın miktarı\b|\byaptırım\w*\b"
        r"|\bcezasında artırım\b"
    ),
    "definition": (
        r"\btanımı nedir\b|\bne demektir\b"
        r"|\bne anlama gelir\b|\bnedir\b"
    ),
    "article_explanation": (
        r"\bmaddesi neyi düzenler\b"
        r"|\bmadde neyi düzenler\b"
        r"|\bmaddenin içeriğini açıklayınız\b"
        r"|\bmaddeyi açıklayınız\b"
    ),
}

PATTERNS = {
    label: re.compile(pattern, re.IGNORECASE)
    for label, pattern in RULES.items()
}

CASE_LAW_ACTION = re.compile(
    r"\byaklaşımı\b|\bgörüşü\b|\bnasıl yorumlan"
    r"|\bgerekçelendir\w*|\bhangi deliller\b"
    r"|\bkararındaki\b|\bkararında nasıl\b"
    r"|\biçtihad\w*",
    re.IGNORECASE,
)

APPLICATION_ACTION = re.compile(
    r"\buygulan\w*|\boluştur\w*|\bsorumlu\b"
    r"|\bkarar verilebilir mi\b|\bengel\b"
    r"|\bhukuki nitelendir\w*|\bgündeme gelir"
    r"|\byararlanabilir mi\b",
    re.IGNORECASE,
)

def classify(question):
    matched = {
        label
        for label, pattern in PATTERNS.items()
        if pattern.search(question)
    }

    if "comparison" in matched:
        return "comparison"

    if (
        "case_law_analysis" in matched
        and CASE_LAW_ACTION.search(question)
    ):
        return "case_law_analysis"

    if (
        "case_application" in matched
        and APPLICATION_ACTION.search(question)
    ):
        return "case_application"

    if "legal_effect" in matched:
        return "legal_effect"

    if "procedure_deadline" in matched:
        return "procedure_deadline"

    if "legal_conditions" in matched:
        return "legal_conditions"

    if "penalty_sanction" in matched:
        return "penalty_sanction"

    if "definition" in matched:
        return "definition"

    if "article_explanation" in matched:
        return "article_explanation"

    return "other"


counts = Counter()
by_split = defaultdict(Counter)
by_law = defaultdict(Counter)
examples = defaultdict(list)
total = 0

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            question = record["messages"][0]["content"]
            law = str(record["metadata"]["law_indicator"])

            label = classify(question)

            counts[label] += 1
            by_split[split][label] += 1
            by_law[law][label] += 1
            total += 1

            if len(examples[label]) < 3:
                examples[label].append({
                    "record_id": record["id"],
                    "question": question[:500],
                    "split": split,
                })

if total != 124510:
    raise ValueError(
        f"124510 kayıt bekleniyordu, {total} bulundu."
    )

with REVIEW.open(encoding="utf-8-sig", newline="") as f:
    reviewed = list(csv.DictReader(f))

if len(reviewed) != 70:
    raise ValueError("70 inceleme kaydı bekleniyordu.")

review_matches = Counter()
review_confusion = defaultdict(Counter)

for row in reviewed:
    expected = row["correct_label"].strip()

    if not expected:
        raise ValueError("Boş inceleme etiketi bulundu.")

    predicted = classify(row["question"])

    review_matches[
        "match" if predicted == expected else "mismatch"
    ] += 1

    review_confusion[expected][predicted] += 1

report = {
    "version": "v0.9.1",
    "method": "revised_question_keyword_heuristics",
    "status": "experimental_not_independently_validated",
    "total": total,
    "distribution": {
        label: {
            "count": count,
            "percent": round(100 * count / total, 2)
        }
        for label, count in counts.most_common()
    },
    "by_split": {
        split: dict(values)
        for split, values in by_split.items()
    },
    "by_law": {
        law: dict(values)
        for law, values in by_law.items()
    },
    "examples": dict(examples),
    "development_sample": {
        "size": len(reviewed),
        "agreement_with_assistant_proposed_labels":
            review_matches["match"],
        "disagreement": review_matches["mismatch"],
        "agreement_percent": round(
            100 * review_matches["match"] / len(reviewed), 2
        ),
        "confusion": {
            expected: dict(predicted)
            for expected, predicted in review_confusion.items()
        },
    },
    "limitations": [
        "Bu yöntem anahtar kelime tabanlıdır.",
        "70 örnek kuralları geliştirmekte kullanılmıştır.",
        "70 örnekteki uyum bağımsız test başarısı değildir.",
        "Örnek etiketler asistan tarafından önerilmiştir.",
        "Yeni ve bağımsız insan etiketli test örneği gereklidir.",
        "Görev etiketleri hukuki cevap doğruluğunu göstermez.",
        "Birincil etiket çok görevli soruları basitleştirir."
    ]
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

if OUTPUT.exists():
    raise SystemExit(
        "Rapor zaten mevcut, üzerine yazılmadı: "
        + str(OUTPUT)
    )

OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("LEXITECH TR - YENİ GÖREV SINIFLANDIRMASI")
print("=" * 60)
print("Toplam QA:", total)

print("\nYENİ GÖREV DAĞILIMI")
for label, count in counts.most_common():
    print(
        f"{label:<25} {count:>7,} "
        f"%{100 * count / total:.2f}"
    )

print("\n70 GELİŞTİRME ÖRNEĞİNDE ETİKET UYUMU")
print("Uyumlu:", review_matches["match"])
print("Uyumsuz:", review_matches["mismatch"])
print(
    "Uyum oranı:",
    f"%{100 * review_matches['match'] / 70:.2f}"
)

print("\nUYARI: Bu bağımsız doğruluk testi değildir.")
print("Rapor:", OUTPUT)
print("Ana veri setleri değiştirilmedi.")

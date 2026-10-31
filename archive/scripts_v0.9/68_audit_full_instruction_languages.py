import json
from collections import Counter
from pathlib import Path

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

ROOT = Path("data/interim/instruction_leakage_clean_v0.9")
OUTPUT = Path(
    "reports/statistics/instruction_language_full_v0.9.json"
)

if OUTPUT.exists():
    raise SystemExit(
        "Rapor zaten mevcut; üzerine yazılmadı: " + str(OUTPUT)
    )

def classify_language(value):
    text = " ".join(str(value).split())

    if len(text) < 30:
        return "uncertain_short", None

    try:
        result = detect_langs(text[:5000])
    except LangDetectException:
        return "uncertain", None

    if not result:
        return "uncertain", None

    best = result[0]

    if best.prob < 0.80:
        return "uncertain", best.lang

    if best.lang == "tr":
        return "tr", "tr"

    return "other_language", best.lang


question_counts = Counter()
answer_counts = Counter()
question_languages = Counter()
answer_languages = Counter()
metadata_languages = Counter()
by_split = {}
flagged = []

total = 0

print("LEXITECH TR - TAM DİL ANALİZİ", flush=True)
print("=" * 60, flush=True)

for split in ("train", "validation", "test"):
    split_q = Counter()
    split_a = Counter()
    split_total = 0

    path = ROOT / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)

            question = record["messages"][0]["content"]
            answer = record["messages"][1]["content"]

            q_category, q_lang = classify_language(question)
            a_category, a_lang = classify_language(answer)

            question_counts[q_category] += 1
            answer_counts[a_category] += 1

            question_languages[q_lang or "unknown"] += 1
            answer_languages[a_lang or "unknown"] += 1

            split_q[q_category] += 1
            split_a[a_category] += 1

            metadata_languages[
                record["metadata"].get("language") or "missing"
            ] += 1

            if q_category != "tr" or a_category != "tr":
                # Metin veya cevapları rapora yazmıyoruz.
                flagged.append({
                    "id": record["id"],
                    "split": split,
                    "question_category": q_category,
                    "question_language": q_lang,
                    "answer_category": a_category,
                    "answer_language": a_lang
                })

            total += 1
            split_total += 1

            if total % 5000 == 0:
                print(
                    f"İncelenen: {total:,} kayıt",
                    flush=True
                )

    by_split[split] = {
        "total": split_total,
        "question_categories": dict(split_q),
        "answer_categories": dict(split_a)
    }

if total != 124510:
    raise ValueError(
        f"124510 kayıt bekleniyordu; {total} bulundu."
    )

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "method": "langdetect_1.0.9",
    "scope": "all_instruction_records",
    "total_records": total,
    "confidence_threshold": 0.80,
    "short_text_threshold": 30,
    "question_categories": dict(question_counts),
    "answer_categories": dict(answer_counts),
    "question_detected_languages": dict(question_languages),
    "answer_detected_languages": dict(answer_languages),
    "metadata_languages": dict(metadata_languages),
    "by_split": by_split,
    "flagged_records": flagged,
    "limitations": [
        "Otomatik dil tespiti hatasız değildir.",
        "30 karakterden kısa metinler belirsiz sayılır.",
        "Karma dilli metinler tek dil etiketi alabilir.",
        "Langdetect olasılığı kalibre edilmiş doğruluk değildir.",
        "İşaretlenen kayıtların manuel kontrolü gereklidir.",
        "Bu analiz hukuki doğruluk veya lisans kanıtı değildir."
    ]
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\nTAM INSTRUCTION DİL ANALİZİ TAMAMLANDI")
print("=" * 60)
print("Toplam kayıt:", total)

print("\nSORU DİLİ")
for category, count in question_counts.most_common():
    print(
        f"{category:<20} {count:>7,} "
        f"%{100 * count / total:.2f}"
    )

print("\nCEVAP DİLİ")
for category, count in answer_counts.most_common():
    print(
        f"{category:<20} {count:>7,} "
        f"%{100 * count / total:.2f}"
    )

print("\nOtomatik kontrol gerektiren QA:", len(flagged))
print("Rapor:", OUTPUT)
print("Ana veri setleri değiştirilmedi.")

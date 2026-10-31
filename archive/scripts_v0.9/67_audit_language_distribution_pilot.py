import json
import random
from collections import Counter
from pathlib import Path

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

DATA = Path("data/interim/instruction_leakage_clean_v0.9")
DOMAIN = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
OUTPUT = Path("reports/statistics/language_distribution_pilot_v0.9.json")

SAMPLE_SIZE = 1200
rng = random.Random(20261028)

def detect(text):
    text = " ".join(str(text).split())

    if len(text) < 30:
        return "uncertain_short", None, 0.0

    try:
        candidates = detect_langs(text[:5000])
        best = candidates[0]
    except (LangDetectException, IndexError):
        return "uncertain", None, 0.0

    language = best.lang
    confidence = best.prob

    if confidence < 0.80:
        category = "uncertain"
    elif language == "tr":
        category = "tr"
    else:
        category = "other_language"

    return category, language, round(confidence, 4)


# 1. Instruction Dataset: bütün havuzdan rastgele örnek.
sample = []
seen = 0
split_counts = Counter()

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            seen += 1
            split_counts[split] += 1

            item = {
                "id": record["id"],
                "split": split,
                "metadata_language":
                    record["metadata"].get("language"),
                "question": record["messages"][0]["content"],
                "answer": record["messages"][1]["content"],
            }

            if len(sample) < SAMPLE_SIZE:
                sample.append(item)
            else:
                index = rng.randrange(seen)
                if index < SAMPLE_SIZE:
                    sample[index] = item

if seen != 124510:
    raise ValueError(f"Beklenen 124510 kayıt, bulunan {seen}")

question_counts = Counter()
answer_counts = Counter()
question_languages = Counter()
answer_languages = Counter()
metadata_counts = Counter()
flagged_examples = []

print("LEXITECH TR - DİL DAĞILIMI ÖN ANALİZİ")
print("=" * 60)
print("Toplam Instruction QA:", seen)
print("Rastgele seçilen QA:", len(sample))

for index, item in enumerate(sample, 1):
    q_category, q_lang, q_score = detect(item["question"])
    a_category, a_lang, a_score = detect(item["answer"])

    question_counts[q_category] += 1
    answer_counts[a_category] += 1
    question_languages[q_lang or "unknown"] += 1
    answer_languages[a_lang or "unknown"] += 1
    metadata_counts[item["metadata_language"] or "missing"] += 1

    if (
        q_category != "tr" or a_category != "tr"
    ) and len(flagged_examples) < 30:
        flagged_examples.append({
            "id": item["id"],
            "split": item["split"],
            "question_category": q_category,
            "question_detected_language": q_lang,
            "question_confidence": q_score,
            "answer_category": a_category,
            "answer_detected_language": a_lang,
            "answer_confidence": a_score,
        })

    if index % 300 == 0:
        print(f"İncelenen QA: {index}/{SAMPLE_SIZE}", flush=True)


# 2. Domain Corpus: her kanundan beş farklı metin penceresi.
domain_documents = 0
domain_passages = 0
domain_counts = Counter()
domain_language_counts = Counter()
domain_metadata = Counter()
domain_details = []

with DOMAIN.open(encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        document = json.loads(line)
        domain_documents += 1

        text = document["text"]
        law = document["law_number"]
        domain_metadata[document.get("language") or "missing"] += 1

        # Başlangıç, dörtte bir, orta, dörtte üç ve son.
        offsets = [
            int(max(0, len(text) - 1500) * p)
            for p in (0, 0.25, 0.5, 0.75, 1)
        ]

        local_counts = Counter()

        for offset in offsets:
            passage = text[offset:offset + 1500]
            category, language, confidence = detect(passage)

            domain_passages += 1
            domain_counts[category] += 1
            domain_language_counts[language or "unknown"] += 1
            local_counts[category] += 1

        domain_details.append({
            "law_number": law,
            "sampled_passages": len(offsets),
            "detection_categories": dict(local_counts)
        })

if domain_documents != 12:
    raise ValueError(
        f"12 Domain belgesi bekleniyordu: {domain_documents}"
    )

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "status": "pilot_sample_not_full_corpus_measurement",
    "method": "langdetect_1.0.9",
    "confidence_threshold": 0.80,
    "instruction": {
        "population": seen,
        "sample_size": len(sample),
        "sampling_method": "reservoir_random_seed_20261028",
        "population_by_split": dict(split_counts),
        "question_categories": dict(question_counts),
        "answer_categories": dict(answer_counts),
        "question_detected_languages": dict(question_languages),
        "answer_detected_languages": dict(answer_languages),
        "sample_metadata_languages": dict(metadata_counts),
        "flagged_example_metadata": flagged_examples
    },
    "domain": {
        "documents": domain_documents,
        "sampled_passages": domain_passages,
        "passage_length_chars": 1500,
        "categories": dict(domain_counts),
        "detected_languages": dict(domain_language_counts),
        "document_metadata_languages": dict(domain_metadata),
        "per_document": domain_details
    },
    "limitations": [
        "Instruction sonuçları 1200 kayıtlık rastgele örneklemdir.",
        "Domain sonuçları her belgeden beş metin parçasına dayanır.",
        "langdetect olasılıkları kalibre edilmiş doğruluk oranları değildir.",
        "Kısa metinlerde otomatik dil tespiti yanılabilir.",
        "Karma dilli metinleri tek bir dil etiketi temsil edebilir.",
        "İnsan doğrulaması henüz yapılmamıştır.",
        "Bu çalışma kullanım hakkını veya hukuki doğruluğu kanıtlamaz."
    ]
}

if OUTPUT.exists():
    raise SystemExit(
        "Rapor zaten mevcut; üzerine yazılmadı: " + str(OUTPUT)
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\nINSTRUCTION - SORU DİLİ")
for key, count in question_counts.most_common():
    print(f"{key:<20} {count:>5}  %{count / SAMPLE_SIZE * 100:.2f}")

print("\nINSTRUCTION - CEVAP DİLİ")
for key, count in answer_counts.most_common():
    print(f"{key:<20} {count:>5}  %{count / SAMPLE_SIZE * 100:.2f}")

print("\nDOMAIN CORPUS - METİN PARÇALARI")
print("Belge:", domain_documents)
print("İncelenen parça:", domain_passages)

for key, count in domain_counts.most_common():
    print(
        f"{key:<20} {count:>5}  "
        f"%{count / domain_passages * 100:.2f}"
    )

print("\nRapor:", OUTPUT)
print("Ana veri setleri değiştirilmedi.")
print("Sonuçlar örnekleme dayalıdır; manuel doğrulama bekliyor.")

import json
import re
from pathlib import Path
from collections import Counter, defaultdict

INPUT = Path("data/deduplicated/exact_unique.jsonl")
OUTPUT = Path(
    "reports/quality/instruction_source_metadata_audit_v0.9.json"
)

source_documents = defaultdict(Counter)
metadata_keys = defaultdict(Counter)
metadata_samples = defaultdict(list)
citation_counts = defaultdict(Counter)
source_counts = Counter()

article_pattern = re.compile(
    r"(?i)\b(?:madde|md\.)\s*\d+"
)

law_pattern = re.compile(
    r"(?i)\b(?:kanun|kanunu|anayasası)\b"
)

with INPUT.open(encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        record = json.loads(line)

        source = str(record.get("source") or "unknown")
        source_counts[source] += 1

        document = record.get("source_document")

        if document is not None and str(document).strip():
            source_documents[source][str(document)] += 1

        metadata = record.get("metadata")

        if isinstance(metadata, dict):
            metadata_keys[source].update(metadata.keys())

            if len(metadata_samples[source]) < 3:
                metadata_samples[source].append({
                    "source_document": document,
                    "metadata": {
                        str(k): str(v)[:250]
                        for k, v in metadata.items()
                    }
                })

        answer = str(record.get("answer") or "")

        if article_pattern.search(answer):
            citation_counts[source]["answer_mentions_article"] += 1

        if law_pattern.search(answer):
            citation_counts[source]["answer_mentions_law"] += 1

report = {
    "source_counts": dict(source_counts),
    "distinct_source_document_counts": {
        source: len(documents)
        for source, documents in source_documents.items()
    },
    "top_source_documents": {
        source: documents.most_common(10)
        for source, documents in source_documents.items()
    },
    "metadata_key_counts": {
        source: dict(keys)
        for source, keys in metadata_keys.items()
    },
    "metadata_samples": dict(metadata_samples),
    "citation_indicator_counts": {
        source: dict(counts)
        for source, counts in citation_counts.items()
    },
    "note": (
        "Atıf göstergeleri doğruluk kanıtı değildir. "
        "Kaynak belge adları resmî hukuk kaynağı "
        "olarak henüz doğrulanmamıştır."
    )
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("LEXITECH TR - INSTRUCTION KAYNAK DENETİMİ")
print("=" * 60)

for source, count in source_counts.items():
    print(f"\nKAYNAK: {source}")
    print("Kayıt sayısı:", count)
    print(
        "Farklı source_document:",
        len(source_documents[source])
    )

    print("En sık görülen 10 belge:")
    for name, frequency in source_documents[source].most_common(10):
        print(f"  {name}: {frequency}")

    print("Metadata anahtarları:")
    for key, frequency in metadata_keys[source].most_common(15):
        print(f"  {key}: {frequency}")

    print(
        "Cevapta madde atfı göstergesi:",
        citation_counts[source]["answer_mentions_article"]
    )
    print(
        "Cevapta kanun ifadesi göstergesi:",
        citation_counts[source]["answer_mentions_law"]
    )

    print("İlk 3 metadata örneği:")
    for sample in metadata_samples[source]:
        print(
            json.dumps(
                sample,
                ensure_ascii=False,
                indent=2
            )
        )

print("\nRapor:", OUTPUT)
print("Kaynak ve hukukî doğruluk henüz onaylanmadı.")
print("Hiçbir soru-cevap kaydı değiştirilmedi.")

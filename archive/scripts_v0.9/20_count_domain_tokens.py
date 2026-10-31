import csv
import json
import statistics
from pathlib import Path

import transformers
import tokenizers
from transformers import AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

INPUT = Path("data/final/domain_corpus_v0.9.jsonl")
OUTPUT = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
REPORT = Path("reports/statistics/domain_token_stats_v0.9.csv")
SUMMARY = Path("reports/statistics/domain_token_summary_v0.9.json")


def percentile(values, percent):
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100

    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return (
        ordered[lower] * (1 - fraction)
        + ordered[upper] * fraction
    )


def main():
    print("LEXITECH TR - DOMAIN CORPUS TOKEN SAYIMI")
    print("-" * 60)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True
    )

    with INPUT.open(encoding="utf-8") as f:
        records = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    if len(records) != 12:
        raise ValueError("12 kanun bekleniyordu.")

    results = []
    token_counts = []

    print("Tokenizer:", MODEL_NAME)
    print("Transformers:", transformers.__version__)
    print("Tokenizers:", tokenizers.__version__)

    print("\nKANUN BAZINDA TOKEN SAYILARI")
    print("-" * 60)

    for record in records:
        text = record["text"]

        if not text.strip():
            raise ValueError(
                f"Boş metin: {record['law_number']}"
            )

        # Metni kesmeden, özel token eklemeden say.
        ids = tokenizer.encode(
            text,
            add_special_tokens=False,
            truncation=False
        )

        count = len(ids)

        record["token_count"] = count
        record["tokenizer_name"] = MODEL_NAME

        token_counts.append(count)

        results.append({
            "law_number": record["law_number"],
            "title": record["title"],
            "char_count": record["char_count"],
            "word_count": record["word_count"],
            "token_count": count
        })

        print(
            record["law_number"],
            "|",
            record["title"],
            "|",
            f"{count:,}",
            "token"
        )

    total = sum(token_counts)

    summary = {
        "dataset": "domain_corpus_v0.9",
        "tokenizer": MODEL_NAME,
        "transformers_version": transformers.__version__,
        "tokenizers_version": tokenizers.__version__,
        "add_special_tokens": False,
        "truncation": False,
        "document_count": len(records),
        "total_tokens": total,
        "min_tokens": min(token_counts),
        "max_tokens": max(token_counts),
        "mean_tokens": round(statistics.mean(token_counts), 2),
        "median_tokens": statistics.median(token_counts),
        "p95_tokens": round(percentile(token_counts, 95), 2)
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(record, ensure_ascii=False)
                + "\n"
            )

    with REPORT.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "law_number",
                "title",
                "char_count",
                "word_count",
                "token_count"
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    with SUMMARY.open("w", encoding="utf-8") as f:
        json.dump(
            summary,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\nGENEL TOKEN İSTATİSTİKLERİ")
    print("-" * 60)

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nOluşturulan dosyalar:")
    print(OUTPUT)
    print(REPORT)
    print(SUMMARY)

    print("\nOrijinal corpus dosyası değiştirilmedi.")


if __name__ == "__main__":
    main()

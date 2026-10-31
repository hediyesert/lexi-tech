import csv
import json
import re
import hashlib
from itertools import combinations
from pathlib import Path

INPUT = Path("data/final/domain_corpus_v0.9.jsonl")
OUTPUT = Path(
    "reports/quality/domain_corpus_near_duplicate_pairs_v0.9.csv"
)

NGRAM_SIZE = 5
THRESHOLD = 0.85


def build_shingles(text):
    words = re.findall(r"\w+", text.casefold())

    result = set()

    for i in range(len(words) - NGRAM_SIZE + 1):
        gram = "\x1f".join(words[i:i + NGRAM_SIZE])

        digest = hashlib.blake2b(
            gram.encode("utf-8"),
            digest_size=8
        ).digest()

        result.add(digest)

    return result


def main():
    with INPUT.open(encoding="utf-8") as f:
        documents = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    if len(documents) != 12:
        raise ValueError("12 kanun bekleniyordu.")

    signatures = {}

    print("LEXITECH TR - NEAR DUPLICATE ANALİZİ")
    print("-" * 55)

    for doc in documents:
        number = doc["law_number"]

        signatures[number] = build_shingles(doc["text"])

        print(
            number,
            "|",
            len(signatures[number]),
            "benzersiz 5-gram"
        )

    results = []

    for a, b in combinations(documents, 2):
        a_number = a["law_number"]
        b_number = b["law_number"]

        set_a = signatures[a_number]
        set_b = signatures[b_number]

        intersection = len(set_a & set_b)
        union = len(set_a) + len(set_b) - intersection

        jaccard = intersection / union if union else 0

        smaller = min(len(set_a), len(set_b))
        containment = intersection / smaller if smaller else 0

        results.append({
            "law_a": a_number,
            "law_b": b_number,
            "jaccard_similarity": round(jaccard, 6),
            "containment_similarity": round(containment, 6),
            "shared_5grams": intersection,
            "near_duplicate": jaccard >= THRESHOLD
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "law_a",
                "law_b",
                "jaccard_similarity",
                "containment_similarity",
                "shared_5grams",
                "near_duplicate"
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    ranked = sorted(
        results,
        key=lambda r: r["jaccard_similarity"],
        reverse=True
    )

    print("\nSONUÇLAR")
    print("-" * 55)
    print("İncelenen belge:", len(documents))
    print("Karşılaştırılan belge çifti:", len(results))
    print("Near duplicate eşiği:", THRESHOLD)

    print(
        "Eşiği aşan çift:",
        sum(r["near_duplicate"] for r in results)
    )

    print("\nEN BENZER 5 KANUN ÇİFTİ")

    for row in ranked[:5]:
        print(
            row["law_a"],
            "-",
            row["law_b"],
            "| Jaccard:",
            row["jaccard_similarity"],
            "| Containment:",
            row["containment_similarity"]
        )

    print("\nRapor:", OUTPUT)
    print("Orijinal veri seti değiştirilmedi.")


if __name__ == "__main__":
    main()

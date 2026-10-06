from pathlib import Path
import hashlib
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"


def create_content_hash(question, answer):
    """
    Temizlenmiş soru + cevap üzerinden SHA-256 content hash üretir.

    Source bilgisi özellikle dahil edilmez.
    Böylece farklı datasetlerdeki aynı içerikler de tespit edilebilir.
    """
    content = f"{question}\n{answer}"

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def main():

    files = sorted(
        CLEANED_DIR.glob("*/train.jsonl")
    )

    seen_hashes = {}

    total = 0
    unique = 0
    duplicates = 0
    cross_source_duplicates = 0

    source_stats = {}

    for file_path in files:

        with open(file_path, "r", encoding="utf-8") as file:

            for line in file:

                record = json.loads(line)

                total += 1

                source = record["source"]

                if source not in source_stats:
                    source_stats[source] = {
                        "total": 0,
                        "duplicates": 0
                    }

                source_stats[source]["total"] += 1

                content_hash = create_content_hash(
                    record["question"],
                    record["answer"]
                )

                if content_hash in seen_hashes:

                    duplicates += 1
                    source_stats[source]["duplicates"] += 1

                    previous_source = seen_hashes[content_hash]

                    if previous_source != source:
                        cross_source_duplicates += 1

                else:
                    seen_hashes[content_hash] = source
                    unique += 1

    print("=" * 70)
    print("EXACT DUPLICATE ANALİZİ")
    print("=" * 70)

    for source, stats in source_stats.items():

        print(f"\nKaynak: {source}")
        print(f"Toplam     : {stats['total']}")
        print(f"Duplicate  : {stats['duplicates']}")

    print("\n" + "=" * 70)
    print(f"Toplam kayıt          : {total}")
    print(f"Unique içerik         : {unique}")
    print(f"Exact duplicate       : {duplicates}")
    print(f"Cross-source duplicate: {cross_source_duplicates}")
    print("=" * 70)


if __name__ == "__main__":
    main()

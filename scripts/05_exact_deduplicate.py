from pathlib import Path
import hashlib
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
OUTPUT_DIR = PROJECT_ROOT / "data" / "deduplicated"


def create_content_hash(question, answer):
    """Temizlenmiş soru + cevap üzerinden SHA-256 üretir."""

    content = f"{question}\n{answer}"

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def main():

    input_files = sorted(
        CLEANED_DIR.glob("*/train.jsonl")
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = OUTPUT_DIR / "exact_unique.jsonl"

    seen_hashes = set()

    total = 0
    kept = 0
    removed = 0

    source_stats = {}

    with open(output_path, "w", encoding="utf-8") as output_file:

        for input_path in input_files:

            with open(input_path, "r", encoding="utf-8") as input_file:

                for line in input_file:

                    record = json.loads(line)

                    total += 1

                    source = record["source"]

                    if source not in source_stats:
                        source_stats[source] = {
                            "total": 0,
                            "kept": 0,
                            "removed": 0,
                        }

                    source_stats[source]["total"] += 1

                    content_hash = create_content_hash(
                        record["question"],
                        record["answer"]
                    )

                    if content_hash in seen_hashes:

                        removed += 1
                        source_stats[source]["removed"] += 1
                        continue

                    seen_hashes.add(content_hash)

                    # Dedup hash'ini provenance amacıyla kayda ekliyoruz.
                    record["content_sha256"] = content_hash

                    json.dump(
                        record,
                        output_file,
                        ensure_ascii=False
                    )

                    output_file.write("\n")

                    kept += 1
                    source_stats[source]["kept"] += 1

    print("=" * 70)
    print("EXACT DEDUPLICATION SONUCU")
    print("=" * 70)

    for source, stats in source_stats.items():

        print(f"\nKaynak: {source}")
        print(f"Giriş     : {stats['total']}")
        print(f"Korunan   : {stats['kept']}")
        print(f"Çıkarılan : {stats['removed']}")

    print("\n" + "=" * 70)
    print(f"Toplam giriş     : {total}")
    print(f"Toplam korunan   : {kept}")
    print(f"Toplam çıkarılan : {removed}")
    print(f"Çıktı            : {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()

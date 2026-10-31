import csv
import json
from collections import Counter
from pathlib import Path

CORPUS = Path(
    "data/final/domain_corpus_v0.9_tokenized.jsonl"
)
PLAN = Path(
    "reports/splits/domain_document_split_v0.9.csv"
)
OUTPUT = Path("data/final/domain_v0.9")

SPLITS = ("train", "validation", "test")

EXPECTED_COUNTS = {
    "train": 10,
    "validation": 1,
    "test": 1
}


def main():
    with CORPUS.open(encoding="utf-8") as f:
        documents = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    with PLAN.open(encoding="utf-8", newline="") as f:
        assignments = list(csv.DictReader(f))

    if len(documents) != 12 or len(assignments) != 12:
        raise ValueError("12 belge ve 12 ayrım kaydı bekleniyor.")

    document_map = {
        d["document_id"]: d
        for d in documents
    }

    if len(document_map) != 12:
        raise ValueError("Tekrarlanan corpus belge ID'si.")

    assigned_ids = [r["document_id"] for r in assignments]

    if len(set(assigned_ids)) != 12:
        raise ValueError("Ayrım planında tekrar eden belge ID'si.")

    if set(assigned_ids) != set(document_map):
        raise ValueError("Corpus ve ayrım planındaki ID'ler farklı.")

    grouped = {split: [] for split in SPLITS}

    for row in assignments:
        split = row["split"]

        if split not in SPLITS:
            raise ValueError(f"Geçersiz split: {split}")

        doc = document_map[row["document_id"]]

        if str(doc["law_number"]) != row["law_number"]:
            raise ValueError("Kanun numarası uyuşmazlığı.")

        if int(doc["token_count"]) != int(row["token_count"]):
            raise ValueError("Token sayısı uyuşmazlığı.")

        record = dict(doc)
        record["split"] = split

        grouped[split].append(record)

    for split, expected in EXPECTED_COUNTS.items():
        if len(grouped[split]) != expected:
            raise ValueError(
                f"{split}: {expected} belge bekleniyordu."
            )

    # Aynı kaynak doküman birden fazla kümede olamaz.
    source_groups = {}

    for split, records in grouped.items():
        for record in records:
            source_id = record["source_document_id"]

            if (
                source_id in source_groups
                and source_groups[source_id] != split
            ):
                raise ValueError(
                    f"Veri sızıntısı: {source_id}"
                )

            source_groups[source_id] = split

    OUTPUT.mkdir(parents=True, exist_ok=True)

    for split, records in grouped.items():
        path = OUTPUT / f"{split}.jsonl"

        with path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(
                    json.dumps(record, ensure_ascii=False)
                    + "\n"
                )

    # Yazılan dosyaları yeniden okuyarak kontrol et.
    verified = {}

    for split in SPLITS:
        path = OUTPUT / f"{split}.jsonl"

        with path.open(encoding="utf-8") as f:
            verified[split] = [
                json.loads(line)
                for line in f
                if line.strip()
            ]

    all_records = [
        record
        for records in verified.values()
        for record in records
    ]

    ids = [r["document_id"] for r in all_records]

    if len(all_records) != 12 or len(set(ids)) != 12:
        raise ValueError("Çıktı bütünlük kontrolü başarısız.")

    print("LEXITECH TR - DOMAIN CORPUS VERİ AYRIMI")
    print("-" * 55)

    total_tokens = sum(r["token_count"] for r in all_records)

    for split in SPLITS:
        records = verified[split]
        tokens = sum(r["token_count"] for r in records)

        print(f"\n{split.upper()}")
        print("Belge sayısı:", len(records))
        print("Token sayısı:", tokens)
        print("Token oranı: %", round(
            tokens / total_tokens * 100, 2
        ))
        print("Dosya:", OUTPUT / f"{split}.jsonl")

    print("\nBÜTÜNLÜK KONTROLÜ")
    print("Toplam belge:", len(all_records))
    print("Benzersiz belge:", len(set(ids)))
    print("Toplam token:", total_tokens)
    print(
        "Split dağılımı:",
        dict(Counter(r["split"] for r in all_records))
    )
    print("Kaynak doküman sızıntısı: 0")
    print("Orijinal corpus değiştirilmedi.")


if __name__ == "__main__":
    main()

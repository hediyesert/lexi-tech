import json
import hashlib
from pathlib import Path
from collections import Counter

SOURCE = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
FOLDER = Path("data/final/domain_v0.9")
REPORT = Path("reports/quality/domain_split_integrity_v0.9.json")

SPLITS = ("train", "validation", "test")


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    original = load_jsonl(SOURCE)

    if len(original) != 12:
        raise ValueError("Orijinal corpus 12 belge içermiyor.")

    source_map = {r["document_id"]: r for r in original}

    if len(source_map) != 12:
        raise ValueError("Orijinal corpus ID'leri benzersiz değil.")

    errors = []
    all_records = []
    counts = Counter()
    token_totals = Counter()

    for split in SPLITS:
        path = FOLDER / f"{split}.jsonl"
        records = load_jsonl(path)

        counts[split] = len(records)

        for record in records:
            doc_id = record["document_id"]
            all_records.append(record)

            if doc_id not in source_map:
                errors.append(f"Bilinmeyen belge: {doc_id}")
                continue

            reference = source_map[doc_id]

            if record.get("split") != split:
                errors.append(f"Split alanı hatalı: {doc_id}")

            restored = dict(record)
            restored.pop("split", None)

            if restored != reference:
                errors.append(f"Belge içeriği/metadata değişmiş: {doc_id}")

            if record["char_count"] != len(record["text"]):
                errors.append(f"Karakter sayısı uyuşmuyor: {doc_id}")

            actual_hash = text_sha256(record["text"])

            if actual_hash != record["text_sha256"]:
                errors.append(f"Metin SHA-256 uyuşmuyor: {doc_id}")

            token_totals[split] += record["token_count"]

    ids = [r["document_id"] for r in all_records]
    source_ids = [r["source_document_id"] for r in all_records]

    if len(ids) != 12 or len(set(ids)) != 12:
        errors.append("Belge sayısı veya benzersizliği hatalı.")

    if set(ids) != set(source_map):
        errors.append("Eksik veya fazladan belge var.")

    if len(set(source_ids)) != len(source_ids):
        errors.append("Kaynak belge farklı kümelerde tekrarlanıyor.")

    original_tokens = sum(r["token_count"] for r in original)
    split_tokens = sum(token_totals.values())

    if original_tokens != split_tokens:
        errors.append("Toplam token sayısı değişmiş.")

    report = {
        "source_file": str(SOURCE),
        "split_folder": str(FOLDER),
        "original_documents": len(original),
        "split_documents": len(all_records),
        "original_tokens": original_tokens,
        "split_tokens": split_tokens,
        "document_counts": dict(counts),
        "token_counts": dict(token_totals),
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL"
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with REPORT.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("LEXITECH TR - DOMAIN SPLIT BÜTÜNLÜK DENETİMİ")
    print("-" * 55)
    print("Orijinal belge:", len(original))
    print("Ayrılmış belge:", len(all_records))
    print("Orijinal token:", original_tokens)
    print("Ayrılmış token:", split_tokens)
    print("Küme belge sayıları:", dict(counts))
    print("Hata sayısı:", len(errors))
    print("Sonuç:", report["status"])
    print("Rapor:", REPORT)

    for error in errors:
        print("HATA:", error)

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

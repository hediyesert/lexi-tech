import csv
import json
import hashlib
from pathlib import Path
from collections import Counter

ROOT = Path("data/final/domain_v0.9")
PLAN = Path("reports/quality/domain_section_plan_v0.9.csv")
REPORT = Path("reports/quality/domain_chunk_integrity_v0.9.json")

SPLITS = ("train", "validation", "test")
LIMIT = 2048


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    with PLAN.open(encoding="utf-8", newline="") as f:
        sections = list(csv.DictReader(f))

    sections_by_doc = {}

    for section in sections:
        sections_by_doc.setdefault(
            section["document_id"], []
        ).append(section)

    errors = []
    ids = set()
    total_chunks = 0
    checked_documents = 0
    section_counts = Counter()
    split_counts = Counter()
    review_count = 0

    for split in SPLITS:
        documents = load_jsonl(ROOT / f"{split}.jsonl")
        chunks = load_jsonl(ROOT / "chunks" / f"{split}.jsonl")

        split_counts[split] = len(chunks)

        by_doc = {}
        for chunk in chunks:
            by_doc.setdefault(chunk["document_id"], []).append(chunk)

        for doc in documents:
            doc_id = doc["document_id"]
            pieces = sorted(
                by_doc.pop(doc_id, []),
                key=lambda c: c["start_char"]
            )

            if not pieces:
                errors.append(f"Chunk bulunamadı: {doc_id}")
                continue

            checked_documents += 1
            position = 0
            reconstructed = []

            doc_sections = sections_by_doc.get(doc_id, [])

            for chunk in pieces:
                total_chunks += 1

                chunk_id = chunk["chunk_id"]

                if chunk_id in ids:
                    errors.append(f"Tekrarlanan chunk ID: {chunk_id}")
                ids.add(chunk_id)

                start = chunk["start_char"]
                end = chunk["end_char"]
                text = chunk["text"]

                if start != position or end <= start:
                    errors.append(f"Konum hatası: {chunk_id}")

                if len(text) != end - start:
                    errors.append(f"Uzunluk hatası: {chunk_id}")

                if text != doc["text"][start:end]:
                    errors.append(f"Metin farklı: {chunk_id}")

                if sha256(text) != chunk["text_sha256"]:
                    errors.append(f"SHA-256 hatası: {chunk_id}")

                if not 0 < chunk["token_count"] <= LIMIT:
                    errors.append(f"Token sınırı hatası: {chunk_id}")

                if chunk["split"] != split:
                    errors.append(f"Split hatası: {chunk_id}")

                if chunk["source_document_id"] != doc["source_document_id"]:
                    errors.append(f"Kaynak hatası: {chunk_id}")

                matching_sections = [
                    s for s in doc_sections
                    if int(s["start_char"]) <= start
                    and end <= int(s["end_char"])
                    and s["section_type"] == chunk["section_type"]
                ]

                if len(matching_sections) != 1:
                    errors.append(f"Bölüm sınırı hatası: {chunk_id}")

                if chunk["section_type"] == "amendment_table":
                    if chunk["training_candidate"] is not False:
                        errors.append(f"Tablo etiketi hatası: {chunk_id}")

                if chunk["requires_manual_review"]:
                    review_count += 1

                section_counts[chunk["section_type"]] += 1
                reconstructed.append(text)
                position = end

            if "".join(reconstructed) != doc["text"]:
                errors.append(f"Belge yeniden oluşturulamadı: {doc_id}")

            if position != len(doc["text"]):
                errors.append(f"Belge sonu hatası: {doc_id}")

            if sha256("".join(reconstructed)) != doc["text_sha256"]:
                errors.append(f"Belge SHA-256 hatası: {doc_id}")

        for unknown_id in by_doc:
            errors.append(f"Fazladan belgeye ait chunk: {unknown_id}")

    if checked_documents != 12:
        errors.append("12 belge doğrulanamadı.")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "document_count": checked_documents,
        "total_chunks": total_chunks,
        "split_counts": dict(split_counts),
        "section_counts": dict(section_counts),
        "manual_review_pending": review_count,
        "max_allowed_tokens": LIMIT,
        "error_count": len(errors),
        "errors": errors
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("LEXITECH TR - CHUNK BÜTÜNLÜK DENETİMİ")
    print("-" * 60)
    print("Doğrulanan belge:", checked_documents)
    print("Toplam chunk:", total_chunks)
    print("Split dağılımı:", dict(split_counts))
    print("Bölüm dağılımı:", dict(section_counts))
    print("Manuel kontrol bekleyen chunk:", review_count)
    print("Hata sayısı:", len(errors))
    print("Sonuç:", report["status"])
    print("Rapor:", REPORT)

    for error in errors[:20]:
        print("HATA:", error)

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

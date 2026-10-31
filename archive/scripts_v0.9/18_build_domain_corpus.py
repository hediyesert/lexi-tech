import csv
import json
import hashlib
from pathlib import Path

INVENTORY = Path("reports/sources/legislation_documents.csv")
OUTPUT = Path("data/final/domain_corpus_v0.9.jsonl")


def sha256_file(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def main():
    with INVENTORY.open(
        encoding="utf-8",
        newline=""
    ) as f:
        documents = list(csv.DictReader(f))

    if len(documents) != 12:
        raise ValueError(
            f"12 kanun bekleniyordu, {len(documents)} bulundu."
        )

    records = []
    seen_ids = set()
    seen_numbers = set()

    for doc in documents:
        document_id = doc["document_id"]
        law_number = doc["law_number"]

        if document_id in seen_ids:
            raise ValueError(f"Tekrarlanan ID: {document_id}")

        if law_number in seen_numbers:
            raise ValueError(f"Tekrarlanan kanun: {law_number}")

        seen_ids.add(document_id)
        seen_numbers.add(law_number)

        raw_path = Path(doc["raw_path"])
        cleaned_path = Path(doc["cleaned_path"])

        if not raw_path.is_file():
            raise FileNotFoundError(raw_path)

        if not cleaned_path.is_file():
            raise FileNotFoundError(cleaned_path)

        if sha256_file(raw_path) != doc["raw_sha256"]:
            raise ValueError(
                f"PDF SHA-256 uyuşmazlığı: {law_number}"
            )

        if sha256_file(cleaned_path) != doc["cleaned_sha256"]:
            raise ValueError(
                f"TXT SHA-256 uyuşmazlığı: {law_number}"
            )

        text = cleaned_path.read_text(encoding="utf-8")

        if not text.strip():
            raise ValueError(f"Boş metin: {law_number}")

        record = {
            "document_id": document_id,
            "source_document_id": document_id,
            "title": doc["law_name"],
            "law_number": law_number,
            "legal_area": doc["legal_area"],
            "language": "tr",
            "document_type": "legislation",
            "source_name": doc["source_name"],
            "source_url": doc["source_url"],
            "document_url": doc["document_url"],
            "access_date": doc["access_date"],
            "raw_sha256": doc["raw_sha256"],
            "text_sha256": doc["cleaned_sha256"],
            "rights_status": doc["rights_status"],
            "quality_status": doc["quality_status"],
            "char_count": len(text),
            "word_count": len(text.split()),
            "text": text
        }

        records.append(record)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(record, ensure_ascii=False)
                + "\n"
            )

    print("LEXITECH TR - DOMAIN CORPUS v0.9")
    print("-" * 55)
    print("Oluşturulan dosya:", OUTPUT)
    print("Toplam belge:", len(records))
    print(
        "Toplam karakter:",
        sum(r["char_count"] for r in records)
    )
    print(
        "Toplam kelime:",
        sum(r["word_count"] for r in records)
    )

    print("\nKANUNLAR")
    for record in records:
        print(
            record["law_number"],
            "|",
            record["title"],
            "|",
            record["char_count"],
            "karakter"
        )

    print("\nKONTROLLER")
    print("Benzersiz belge ID:", len(seen_ids))
    print("Benzersiz kanun numarası:", len(seen_numbers))
    print(
        "İnsan incelemesi bekleyen:",
        sum(
            r["quality_status"]
            == "otomatik_temizlik_yapildi_insan_kontrolu_bekliyor"
            for r in records
        )
    )
    print(
        "Kullanım hakları incelemesi bekleyen:",
        sum(
            r["rights_status"] == "incelenecek"
            for r in records
        )
    )
    print(
        "Doğrudan belge URL'si eksik:",
        sum(not r["document_url"] for r in records)
    )

    print("\nOrijinal TXT ve PDF dosyaları değiştirilmedi.")


if __name__ == "__main__":
    main()

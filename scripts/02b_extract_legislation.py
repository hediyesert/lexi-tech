"""Kanun PDF'lerinden metin çıkarır ve çıkarım başarısını ölçer.

PDF'ler 19-20 Ekim 2026'da mevzuat.gov.tr sayfalarından tarayıcıyla PDF olarak
kaydedildi; bu yüzden indirme adımı script değildir. Bütünlük, envanterdeki
SHA-256 değerleriyle doğrulanır. Belgeye özel URL sayfa altbilgisinden okunur.
"""
import csv
import logging
import re
from statistics import median

from pypdf import PdfReader

from common import INVENTORY, load_config, load_inventory, path_of, sha256_file, write_json

logging.disable(logging.CRITICAL)

FOOTER = re.compile(
    r"(\d{2}\.\d{2}\.\d{4})\s+\d{2}:\d{2}(?:\d{4})?\s*\n"
    r"Sayfa\s+1\s*/\s*(\d+)\s*(https://www\.mevzuat\.gov\.tr/\S+)"
)


def footer_url(url):
    # PDF yazı tipi "i" harfini çift tırnak olarak veriyor: MevzuatF"hr"st.
    return url.replace('"', "i")


def main():
    config = load_config()
    rows = load_inventory()
    min_chars = config["extraction"]["min_chars_per_page"]
    output_dir = path_of(config["paths"]["extracted"], "legislation")
    output_dir.mkdir(parents=True, exist_ok=True)

    documents = []

    for row in rows:
        raw_path = path_of(row["raw_path"])

        if sha256_file(raw_path) != row["raw_sha256"]:
            raise ValueError(f"Ham PDF değişmiş: {raw_path}")

        pages = [
            page.extract_text() or ""
            for page in PdfReader(raw_path).pages
        ]
        text = "\n\n".join(pages)
        (output_dir / f"{raw_path.stem}.txt").write_text(text, encoding="utf-8")

        match = FOOTER.search(text)
        if not match or int(match.group(2)) != len(pages):
            raise ValueError(f"Altbilgi okunamadı: {raw_path}")

        date = match.group(1)
        row["document_url"] = footer_url(match.group(3))
        row["version_date"] = f"{date[6:]}-{date[3:5]}-{date[:2]}"

        lengths = [len(page.strip()) for page in pages]
        low_text_pages = [
            number
            for number, length in enumerate(lengths, start=1)
            if length < min_chars
        ]

        # Son sayfanın kısa olması normaldir; ayrıca sayılmaz.
        failed = [p for p in low_text_pages if p != len(pages)]

        documents.append({
            "law_number": row["law_number"],
            "file": raw_path.name,
            "pages": len(pages),
            "characters": len(text),
            "median_chars_per_page": median(lengths),
            "low_text_pages": low_text_pages,
            "needs_ocr": bool(failed),
        })
        print(f"{raw_path.name}: {len(pages)} sayfa, {len(text):,} karakter")

    fieldnames = list(rows[0].keys())
    with INVENTORY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    failed_documents = sum(d["needs_ocr"] for d in documents)
    write_json(path_of(config["paths"]["reports"], "statistics/legislation_extraction_v1.0.json"), {
        "tool": "pypdf",
        "documents_total": len(documents),
        "documents_failed": failed_documents,
        "failure_rate": failed_documents / len(documents),
        "pages_total": sum(d["pages"] for d in documents),
        "min_chars_per_page": min_chars,
        "documents": documents,
    })
    print("Başarısız doküman:", failed_documents)


if __name__ == "__main__":
    main()

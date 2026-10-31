"""İnsan kalite kontrolü için Excel dosyası üretir ve sonuçları geri alır.

    python scripts/qc_review_sheet.py export
    python scripts/qc_review_sheet.py import

Excel'de yalnızca sarı sütunlar doldurulur. Sonuçlar CSV örneklemlerine işlenir;
asistan sütunlarına dokunulmaz. İnceleyen adı olmayan satır sayılmaz.
"""
import argparse
import csv
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from common import build_article_index, load_config, path_of, read_jsonl

CELL_LIMIT = 32000
YELLOW = PatternFill("solid", fgColor="FFF2CC")
HEADER = PatternFill("solid", fgColor="D9E1F2")

DOMAIN_CHECKS = [
    ("human_readable", "Metin okunabiliyor mu?"),
    ("human_in_domain", "Hukuk alanıyla ilgili mi?"),
    ("human_extraction_ok", "Metin doğru çıkarılmış mı?"),
    ("human_header_footer_clean", "Başlık/altbilgi kalıntısı yok mu?"),
    ("human_no_broken_chars", "Bozuk karakter yok mu?"),
    ("human_metadata_ok", "Kanun numarası doğru mu?"),
]
INSTRUCTION_CHECKS = [
    ("human_clear_instruction", "Soru anlaşılır mı?"),
    ("human_matches_source", "Cevap kaynakla tutarlı mı?"),
    ("human_answers_instruction", "Cevap soruyu karşılıyor mu?"),
    ("human_task_type_ok", "Görev türü doğru mu?"),
]


def quality_dir(config):
    return path_of(config["paths"]["reports"], "quality")


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_sheet(book, title, columns, rows, checks):
    """columns: (başlık, genişlik) listesi; rows: aynı sıradaki değerler."""
    sheet = book.create_sheet(title)
    check_labels = [label for _, label in checks]
    headers = [c[0] for c in columns] + check_labels + ["İnceleyen (adınız)", "Not"]
    sheet.append(headers)

    for row in rows:
        sheet.append([value[:CELL_LIMIT] for value in row])

    for index, (_, width) in enumerate(columns, start=1):
        sheet.column_dimensions[sheet.cell(1, index).column_letter].width = width

    first_input = len(columns) + 1
    last_input = len(headers)
    validation = DataValidation(type="list", formula1='"yes,no"', allow_blank=True)
    sheet.add_data_validation(validation)
    for column in range(first_input, last_input + 1):
        letter = sheet.cell(1, column).column_letter
        sheet.column_dimensions[letter].width = 16
        for line in range(2, len(rows) + 2):
            sheet.cell(line, column).fill = YELLOW
        if column < first_input + len(check_labels):
            validation.add(f"{letter}2:{letter}{len(rows) + 1}")

    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER
    for line in sheet.iter_rows():
        for cell in line:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "B2"


def export_sheet(config, output):
    quality = quality_dir(config)
    final_dir = path_of(config["paths"]["final"])
    index = {
        d["law_number"]: build_article_index(d)
        for d in read_jsonl(final_dir / "domain_corpus_v1.0.jsonl")
    }
    chunks = {
        c["chunk_id"]: c
        for split in ("train", "validation", "test")
        for c in read_jsonl(final_dir / f"{split}.jsonl")
    }

    def source_text(articles):
        if not articles:
            return "Kaynak madde yok: alan dışı veya sınır örneği. Cevabın sınırını doğru söylediğine bakın."
        parts = []
        for citation in articles.split(";"):
            law, key = citation.split(":")
            parts.append(f"[{citation}]\n{index[law][key]['text']}")
        return "\n\n".join(parts)

    priority = {"needs_legal_review": 0, "not_reviewed": 1, "rule_checked": 3}
    samples = sorted(
        read_rows(quality / "qc_instruction_sample_v1.0.csv"),
        key=lambda r: priority.get(r["assistant_verdict"], 2),
    )
    instruction = [
        [r["id"], r["assistant_verdict"], r["assistant_note"], r["task_type"], r["source_articles"],
         r["instruction"], r["response"], source_text(r["source_articles"])]
        for r in samples
    ]
    domain = []
    missing = 0
    domain_rows = sorted(
        read_rows(quality / "qc_domain_sample_v1.0.csv"),
        key=lambda r: not r["assistant_note"],
    )
    for row in domain_rows:
        chunk = chunks.get(row["chunk_id"])
        if chunk is None:
            missing += 1
            continue
        domain.append([row["chunk_id"], row["assistant_note"], row["law_number"], chunk["title"], chunk["text"]])

    book = Workbook()
    guide = book.active
    guide.title = "Nasıl yapılır"
    for line in [
        "Her satırı okuyun, sarı sütunlara yes veya no yazın, İnceleyen sütununa adınızı yazın.",
        "Instruction: cevabı yandaki kaynak maddeyle karşılaştırın. Emin değilseniz no deyip Not'a yazın.",
        "Asistan sütunları yalnızca öneridir. Şüpheli satırlar üsttedir. Kararı siz verirsiniz.",
        "Domain: metin okunabilir mi, kalıntı var mı diye bakın.",
        "Bitince dosyayı kaydedin, ardından: python scripts/qc_review_sheet.py import",
    ]:
        guide.append([line])
    guide.column_dimensions["A"].width = 110

    build_sheet(
        book,
        "Instruction",
        [("ID", 11), ("Asistan görüşü", 18), ("Asistan notu", 30), ("Görev", 16), ("Madde", 14), ("Soru", 45), ("Cevap", 60), ("Kaynak madde metni", 70)],
        instruction,
        INSTRUCTION_CHECKS,
    )
    build_sheet(
        book,
        "Domain",
        [("Chunk", 26), ("Asistan notu", 30), ("Kanun", 8), ("Başlık", 24), ("Metin", 100)],
        domain,
        DOMAIN_CHECKS,
    )
    book.save(output)
    print(f"Yazıldı: {output} ({len(instruction)} instruction, {len(domain)} domain, eksik chunk {missing})")


def import_sheet(config, source):
    quality = quality_dir(config)
    book = load_workbook(source, read_only=True)

    def collect(sheet_name, checks, csv_name, key):
        path = quality / csv_name
        rows = read_rows(path)
        by_key = {r[key]: r for r in rows}
        lines = book[sheet_name].iter_rows(values_only=True)
        headers = list(next(lines))
        labels = [(field, headers.index(label)) for field, label in checks]
        reviewer_at = headers.index("İnceleyen (adınız)")
        applied = 0
        for line in lines:
            row = by_key.get(line[0])
            reviewer = line[reviewer_at]
            if row is None or not reviewer:
                continue
            for field, position in labels:
                value = (line[position] or "").strip().lower()
                if value not in ("", "yes", "no"):
                    raise ValueError(f"{line[0]}: yalnızca yes/no yazılabilir, bulunan: {value}")
                row[field] = value
            row["human_reviewer"] = str(reviewer).strip()
            applied += 1
        write_rows(path, rows)
        print(f"{sheet_name}: {applied} satır işlendi")
        return rows

    instruction = collect(
        "Instruction", INSTRUCTION_CHECKS, "qc_instruction_sample_v1.0.csv", "id"
    )
    collect("Domain", DOMAIN_CHECKS, "qc_domain_sample_v1.0.csv", "chunk_id")

    failed = [r["id"] for r in instruction if r["human_matches_source"] == "no"]
    if failed:
        print("Kaynakla tutarsız işaretlenen kayıtlar (qc_rejected_ids_v1.0.txt için):")
        records = {
            e["id"]: e
            for e in read_jsonl(path_of(config["paths"]["final"], "instruction_v1.0.jsonl"))
        }
        for identifier in failed:
            print(identifier, records[identifier]["origin"].get("record_id"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["export", "import"])
    parser.add_argument("--file", default="reports/quality/kalite_inceleme_v1.0.xlsx")
    arguments = parser.parse_args()

    config = load_config()
    target = Path(arguments.file)
    if not target.is_absolute():
        target = path_of(arguments.file)

    if arguments.action == "export":
        if target.exists():
            raise SystemExit(f"Dosya zaten var, üzerine yazılmadı: {target}")
        export_sheet(config, target)
    else:
        import_sheet(config, target)


if __name__ == "__main__":
    main()

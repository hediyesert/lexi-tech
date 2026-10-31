"""Domain Corpus v1.0 adayını kurar: doküman kaydı, metadata, split ve chunk.

Split dokümanın düzeyinde yapılır (reports/splits/domain_document_split_v1.0.csv),
chunk'lar split'ten sonra üretilir. Bir chunk asla iki kümeye düşmez.
Değişiklik tabloları kanun hükmü olmadığı için eğitim dosyalarına alınmaz.
"""
import csv
import re
from collections import Counter

from langdetect import DetectorFactory, detect
from transformers import AutoTokenizer

from common import (
    ARTICLE_HEADING,
    load_config,
    load_inventory,
    path_of,
    sha256_text,
    write_json,
    write_jsonl,
)

DetectorFactory.seed = 42

SUBTOPICS = {
    "constitutional_law": "anayasa_hukuku",
    "civil_law": "medeni_hukuk",
    "obligations_law": "borclar_hukuku",
    "criminal_law": "ceza_hukuku",
    "criminal_procedure": "ceza_muhakemesi",
    "labor_law": "is_hukuku",
    "commercial_law": "ticaret_hukuku",
    "consumer_law": "tuketici_hukuku",
    "administrative_law": "idare_hukuku",
    "tax_law": "vergi_hukuku",
    "enforcement_law": "icra_iflas_hukuku",
    "social_security_law": "sosyal_guvenlik_hukuku",
}

ANNOTATION = re.compile(r"(?m)^(?=\((?:Ek|Değişik|Mülga|Yeniden düzenlenen)\b)")
SENTENCE_END = re.compile(r'[.!?]["”’)]{0,2}(?:\n| )')


def load_sections(config, row, text):
    """Bölüm sınırlarını boşluk dışı karakter sayısından metin konumuna çevirir.

    Sınırlar reports/sources/domain_sections_v1.0.csv içinde boşluktan bağımsız
    tutulur; böylece boşluk temizliği bölüm sınırlarını kaydırmaz.
    """
    path = path_of(config["paths"]["reports"], "sources/domain_sections_v1.0.csv")
    with path.open(encoding="utf-8", newline="") as f:
        plan = [p for p in csv.DictReader(f) if p["document_id"] == row["document_id"]]

    wanted = sorted({int(p[k]) for p in plan for k in ("start_nonspace", "end_nonspace")})
    positions = {}
    count = 0
    pointer = 0
    for position, char in enumerate(text):
        while pointer < len(wanted) and wanted[pointer] == count:
            positions[wanted[pointer]] = position
            pointer += 1
        if not char.isspace():
            count += 1
    for value in wanted[pointer:]:
        positions[value] = len(text)

    return [
        {
            "section_type": p["section_type"],
            "start_char": positions[int(p["start_nonspace"])],
            "end_char": positions[int(p["end_nonspace"])],
        }
        for p in plan
    ]


def publication_year(text):
    match = re.search(r"Kabul Tarihi\s*:\s*\d{1,2}/\d{1,2}/(\d{4})", text)
    return int(match.group(1))


def caption_start(text, heading, lower_bound):
    """Madde başlığı bir önceki satırdaysa chunk sınırını onun önüne alır."""
    previous_end = heading - 1
    previous_start = text.rfind("\n", 0, previous_end) + 1
    line = text[previous_start:previous_end]
    if previous_start > lower_bound and len(line) < 120 and not line.endswith((".", ";", ",")):
        return previous_start
    return heading


def legal_units(text, start, end):
    """Bölümü madde başlarından kayıpsız birimlere ayırır."""
    starts = [start]
    for match in ARTICLE_HEADING.finditer(text, start, end):
        if match.start() > start:
            starts.append(caption_start(text, match.start(), starts[-1]))
    return list(zip(starts, starts[1:] + [end]))


def split_long_unit(text, start, end, max_tokens, count_tokens):
    """Tek başına sınırı aşan maddeyi not, satır, cümle ve kelime sınırından böler."""
    pieces = []
    cursor = start

    while cursor < end:
        low, high, best = cursor + 1, end, cursor
        while low <= high:
            middle = (low + high) // 2
            if count_tokens(text[cursor:middle]) <= max_tokens:
                best, low = middle, middle + 1
            else:
                high = middle - 1

        if best == end:
            pieces.append((cursor, end))
            break

        floor = cursor + (best - cursor) // 2
        window = text[floor:best]
        candidates = (
            [floor + m.start() for m in ANNOTATION.finditer(window) if m.start() > 0],
            [floor + m.end() for m in SENTENCE_END.finditer(window)],
            [floor + m.end() for m in re.finditer(r"\n", window)],
            [floor + m.end() for m in re.finditer(r" ", window)],
        )
        cut = next((c[-1] for c in candidates if c), best)
        pieces.append((cursor, cut))
        cursor = cut

    return pieces


def chunk_section(text, section, max_tokens, count_tokens):
    """Maddeleri sınırı aşmadan birleştirir; uzun maddeyi ayrıca böler."""
    chunks = []
    current_start = None
    current_end = None

    for start, end in legal_units(text, section["start_char"], section["end_char"]):
        if current_start is not None and count_tokens(text[current_start:end]) <= max_tokens:
            current_end = end
            continue

        if current_start is not None:
            chunks.append((current_start, current_end))
            current_start = None

        if count_tokens(text[start:end]) <= max_tokens:
            current_start, current_end = start, end
        else:
            pieces = split_long_unit(text, start, end, max_tokens, count_tokens)
            chunks.extend(pieces[:-1])
            current_start, current_end = pieces[-1]

    if current_start is not None:
        chunks.append((current_start, current_end))

    return chunks


def main():
    config = load_config()
    tokenizer = AutoTokenizer.from_pretrained(config["tokenizer"], use_fast=True)
    max_tokens = config["domain"]["max_chunk_tokens"]
    final_dir = path_of(config["paths"]["final"])
    version = config["project"]["version"]

    def count_tokens(value):
        return len(tokenizer.encode(value, add_special_tokens=False, truncation=False))

    with path_of(config["paths"]["reports"], "splits/domain_document_split_v1.0.csv").open(
        encoding="utf-8", newline=""
    ) as f:
        split_of = {row["document_id"]: row["split"] for row in csv.DictReader(f)}

    documents = []
    chunks = {"train": [], "validation": [], "test": []}
    excluded = []

    for row in load_inventory():
        stem = path_of(row["raw_path"]).stem
        text = path_of(config["paths"]["cleaned"], "legislation_v1.0", f"{stem}.txt").read_text(
            encoding="utf-8"
        )
        sections = load_sections(config, row, text)
        split = split_of[row["document_id"]]
        subtopic = SUBTOPICS[row["legal_area"]]

        documents.append({
            "document_id": row["document_id"],
            "title": row["law_name"],
            "law_number": row["law_number"],
            "source": row["source_name"],
            "url": row["document_url"],
            "language": "tr",
            "document_type": "kanun",
            "publication_year": publication_year(text),
            "version_date": row["version_date"],
            "access_date": row["access_date"],
            "subtopic": subtopic,
            "split": split,
            "raw_sha256": row["raw_sha256"],
            "text_sha256": sha256_text(text),
            "rights_status": "pending_review",
            "char_count": len(text),
            "word_count": len(text.split()),
            "token_count": count_tokens(text),
            "tokenizer_name": config["tokenizer"],
            "sections": sections,
            "text": text,
        })

        number = 0
        for section in sections:
            for start, end in chunk_section(text, section, max_tokens, count_tokens):
                body = text[start:end].strip()
                if not body:
                    continue
                number += 1
                chunk = {
                    "chunk_id": f"{row['document_id']}_chunk_{number:05d}",
                    "document_id": row["document_id"],
                    "title": row["law_name"],
                    "law_number": row["law_number"],
                    "source": row["source_name"],
                    "url": row["document_url"],
                    "language": detect(body[:2000]),
                    "subtopic": subtopic,
                    "split": split,
                    "section_type": section["section_type"],
                    "start_char": start,
                    "end_char": end,
                    "char_count": len(body),
                    "token_count": count_tokens(body),
                    "dataset_version": version,
                    "training_approved": False,
                    "text": body,
                }
                if section["section_type"] == "amendment_table":
                    chunk["exclusion_reason"] = "amendment_table"
                    excluded.append(chunk)
                else:
                    chunks[split].append(chunk)

        print(row["document_id"], split, documents[-1]["token_count"])

    write_jsonl(final_dir / "domain_corpus_v1.0.jsonl", documents)
    for split, records in chunks.items():
        write_jsonl(final_dir / f"{split}.jsonl", records)
    write_jsonl(path_of("data/interim/domain_excluded_chunks_v1.0.jsonl"), excluded)

    write_json(path_of(config["paths"]["reports"], "statistics/domain_build_v1.0.json"), {
        "documents": len(documents),
        "chunks_by_split": {k: len(v) for k, v in chunks.items()},
        "chunks_excluded": dict(Counter(c["exclusion_reason"] for c in excluded)),
        "chunk_languages": dict(Counter(
            c["language"] for records in chunks.values() for c in records
        )),
        "max_chunk_tokens": max_tokens,
    })
    print({k: len(v) for k, v in chunks.items()}, "dışlanan:", len(excluded))


if __name__ == "__main__":
    main()

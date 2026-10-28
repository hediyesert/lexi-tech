import csv
import json
import re
import hashlib
from pathlib import Path
from collections import Counter

from transformers import AutoTokenizer

MODEL = "Qwen/Qwen2.5-3B-Instruct"
MAX_TOKENS = 2048

ROOT = Path("data/final/domain_v0.9")
PLAN = Path("reports/quality/domain_section_plan_v0.9.csv")
OUTPUT = ROOT / "chunks"
REPORT = Path("reports/statistics/domain_chunk_stats_v0.9.json")

SPLITS = ("train", "validation", "test")

HEADING = re.compile(
    r"(?im)^[ \t]*(?:(?:mükerrer|ek|geçici)[ \t]+)?"
    r"madde[ \t]+\d+(?=[ \t.\-–—]|$)"
)


def sha256(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def make_units(text, start, end, section_type):
    """Metni kayıpsız, anlamlı başlangıç noktalarına ayır."""

    if section_type == "amendment_table":
        # Tablo satırları bağımsız kanun maddesi sayılmaz.
        starts = [start]
        pos = start

        while pos < end:
            newline = text.find("\n", pos, end)

            if newline == -1:
                break

            pos = newline + 1

            if pos < end:
                starts.append(pos)

    else:
        starts = [start]

        for match in HEADING.finditer(text, start, end):
            if match.start() > start:
                starts.append(match.start())

    starts = sorted(set(starts))
    stops = starts[1:] + [end]

    return list(zip(starts, stops))


def main():
    print("LEXITECH TR - HUKUKİ METİN CHUNKING")
    print("-" * 60)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL,
        use_fast=True
    )

    with PLAN.open(encoding="utf-8", newline="") as f:
        plan = list(csv.DictReader(f))

    if len(plan) != 33:
        raise ValueError("33 bölüm planı kaydı bekleniyor.")

    grouped_plan = {}

    for row in plan:
        grouped_plan.setdefault(
            row["document_id"], []
        ).append(row)

    def count_tokens(value):
        return len(tokenizer.encode(
            value,
            add_special_tokens=False,
            truncation=False
        ))

    def split_oversized(text, start, end):
        """Çok uzun bir maddeyi token sınırını aşmadan böl."""

        pieces = []
        cursor = start

        while cursor < end:
            low = cursor + 1
            high = end
            best = cursor

            while low <= high:
                mid = (low + high) // 2

                tokens = count_tokens(text[cursor:mid])

                if tokens <= MAX_TOKENS:
                    best = mid
                    low = mid + 1
                else:
                    high = mid - 1

            if best == cursor:
                raise ValueError(
                    "Token sınırında ilerleme sağlanamadı."
                )

            cut = best

            if best < end:
                halfway = cursor + (best - cursor) // 2

                newline = text.rfind(
                    "\n", cursor, best + 1
                )

                if newline >= halfway:
                    cut = newline + 1
                else:
                    space = text.rfind(
                        " ", cursor, best + 1
                    )

                    if space >= halfway:
                        cut = space + 1

            if cut <= cursor:
                raise ValueError("Geçersiz parça sınırı.")

            pieces.append((cursor, cut))
            cursor = cut

        return pieces

    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    all_chunks = []
    document_summary = []
    oversized_unit_count = 0

    for split in SPLITS:
        documents = load_jsonl(ROOT / f"{split}.jsonl")
        split_chunks = []

        for doc in documents:
            text = doc["text"]
            document_id = doc["document_id"]

            sections = sorted(
                grouped_plan.get(document_id, []),
                key=lambda r: int(r["start_char"])
            )

            if not sections:
                raise ValueError(
                    f"Bölüm planı bulunamadı: {document_id}"
                )

            boundaries = []
            current_position = 0

            for section in sections:
                start = int(section["start_char"])
                end = int(section["end_char"])
                kind = section["section_type"]

                if start != current_position or end <= start:
                    raise ValueError(
                        f"Bölüm sınırı hatası: {document_id}"
                    )

                section_text = text[start:end]

                if sha256(section_text) != section["section_sha256"]:
                    raise ValueError(
                        f"Bölüm SHA-256 hatası: {document_id}"
                    )

                current_position = end

                units = make_units(
                    text, start, end, kind
                )

                if not units:
                    raise ValueError(
                        f"Boş bölüm: {document_id}"
                    )

                cursor_start = None
                cursor_end = None

                def flush():
                    nonlocal cursor_start, cursor_end

                    if cursor_start is None:
                        return

                    boundaries.append((
                        cursor_start,
                        cursor_end,
                        kind
                    ))

                    cursor_start = None
                    cursor_end = None

                for unit_start, unit_end in units:
                    unit_tokens = count_tokens(
                        text[unit_start:unit_end]
                    )

                    if unit_tokens > MAX_TOKENS:
                        oversized_unit_count += 1
                        flush()

                        pieces = split_oversized(
                            text, unit_start, unit_end
                        )

                        for a, b in pieces:
                            boundaries.append((a, b, kind))

                        continue

                    if cursor_start is None:
                        cursor_start = unit_start
                        cursor_end = unit_end
                        continue

                    candidate_tokens = count_tokens(
                        text[cursor_start:unit_end]
                    )

                    if candidate_tokens <= MAX_TOKENS:
                        cursor_end = unit_end
                    else:
                        flush()
                        cursor_start = unit_start
                        cursor_end = unit_end

                flush()

            if current_position != len(text):
                raise ValueError(
                    f"Belge sonu uyuşmuyor: {document_id}"
                )

            reconstructed = []
            position = 0
            document_chunks = []

            for start, end, kind in boundaries:
                if start != position or end <= start:
                    raise ValueError(
                        f"Chunk sıralaması hatalı: {document_id}"
                    )

                piece = text[start:end]
                token_count = count_tokens(piece)

                if token_count > MAX_TOKENS:
                    raise ValueError(
                        f"Chunk token sınırını aştı: {document_id}"
                    )

                chunk = {
                    "chunk_id": (
                        f"{document_id}_chunk_"
                        f"{len(document_chunks) + 1:05d}"
                    ),
                    "document_id": document_id,
                    "source_document_id": doc["source_document_id"],
                    "law_number": doc["law_number"],
                    "title": doc["title"],
                    "legal_area": doc["legal_area"],
                    "language": "tr",
                    "split": split,
                    "section_type": kind,
                    "start_char": start,
                    "end_char": end,
                    "char_count": len(piece),
                    "token_count": token_count,
                    "tokenizer_name": MODEL,
                    "text_sha256": sha256(piece),
                    "requires_manual_review": True,
                    "training_candidate": kind != "amendment_table",
                    "text": piece
                }

                document_chunks.append(chunk)
                reconstructed.append(piece)
                position = end

            rebuilt_text = "".join(reconstructed)

            if rebuilt_text != text:
                raise ValueError(
                    f"Metin kaybı veya değişikliği: {document_id}"
                )

            if sha256(rebuilt_text) != doc["text_sha256"]:
                raise ValueError(
                    f"Belge SHA-256 uyuşmazlığı: {document_id}"
                )

            split_chunks.extend(document_chunks)

            document_summary.append({
                "document_id": document_id,
                "law_number": doc["law_number"],
                "split": split,
                "chunk_count": len(document_chunks),
                "original_tokens": doc["token_count"],
                "chunk_token_sum": sum(
                    c["token_count"]
                    for c in document_chunks
                ),
                "sha256_verified": True
            })

            print(
                f"{doc['law_number']} | {split} | "
                f"{len(document_chunks)} chunk | SHA-256 OK"
            )

        # Bütün kontroller tamamlandıktan sonra kaydet.
        output_path = OUTPUT / f"{split}.jsonl"

        with output_path.open("w", encoding="utf-8") as f:
            for chunk in split_chunks:
                f.write(
                    json.dumps(chunk, ensure_ascii=False)
                    + "\n"
                )

        all_chunks.extend(split_chunks)

    chunk_counts = Counter(
        c["split"] for c in all_chunks
    )

    section_counts = Counter(
        c["section_type"] for c in all_chunks
    )

    summary = {
        "version": "v0.9",
        "tokenizer": MODEL,
        "max_chunk_tokens": MAX_TOKENS,
        "document_count": len(document_summary),
        "total_chunks": len(all_chunks),
        "chunks_per_split": dict(chunk_counts),
        "chunks_per_section": dict(section_counts),
        "oversized_units_split": oversized_unit_count,
        "max_actual_chunk_tokens": max(
            c["token_count"] for c in all_chunks
        ),
        "all_documents_sha256_verified": all(
            d["sha256_verified"] for d in document_summary
        ),
        "documents": document_summary
    }

    with REPORT.open("w", encoding="utf-8") as f:
        json.dump(
            summary,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\nGENEL SONUÇLAR")
    print("-" * 60)
    print("Toplam belge:", summary["document_count"])
    print("Toplam chunk:", summary["total_chunks"])
    print("Split dağılımı:", dict(chunk_counts))
    print("Bölüm dağılımı:", dict(section_counts))
    print(
        "Uzun olduğu için bölünen birim:",
        oversized_unit_count
    )
    print(
        "En uzun chunk:",
        summary["max_actual_chunk_tokens"],
        "token"
    )
    print(
        "Bütün belgelerin SHA-256 doğrulaması:",
        summary["all_documents_sha256_verified"]
    )
    print("Rapor:", REPORT)


if __name__ == "__main__":
    main()

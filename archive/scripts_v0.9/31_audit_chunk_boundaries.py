import csv
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("data/final/domain_v0.9")
REPORT = Path(
    "reports/quality/domain_chunk_boundary_candidates_v0.9.csv"
)

HEADING = re.compile(
    r"(?i)^(?:(?:mükerrer|ek|geçici)\s+)?"
    r"madde\s+\d+(?=[\s.\-–—]|$)"
)


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


candidates = []
counts = Counter()

for split in ("train", "validation", "test"):
    chunks = load_jsonl(
        ROOT / "chunks" / f"{split}.jsonl"
    )

    by_doc = {}

    for chunk in chunks:
        by_doc.setdefault(
            chunk["document_id"], []
        ).append(chunk)

    for doc_id, pieces in by_doc.items():
        pieces.sort(key=lambda x: x["start_char"])

        for previous, current in zip(
            pieces, pieces[1:]
        ):
            if (
                previous["section_type"] != "main_law"
                or current["section_type"] != "main_law"
            ):
                continue

            beginning = current["text"].lstrip()

            if HEADING.match(beginning):
                continue

            boundary_text_before = previous["text"][-120:]
            boundary_text_after = current["text"][:120]

            row = {
                "law_number": current["law_number"],
                "document_id": doc_id,
                "split": split,
                "previous_chunk": previous["chunk_id"],
                "next_chunk": current["chunk_id"],
                "boundary_char": current["start_char"],
                "previous_ends_with": repr(
                    boundary_text_before
                ),
                "next_starts_with": repr(
                    boundary_text_after
                ),
                "manual_status": "pending"
            }

            candidates.append(row)
            counts[current["law_number"]] += 1

REPORT.parent.mkdir(parents=True, exist_ok=True)

with REPORT.open(
    "w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "law_number",
            "document_id",
            "split",
            "previous_chunk",
            "next_chunk",
            "boundary_char",
            "previous_ends_with",
            "next_starts_with",
            "manual_status"
        ]
    )
    writer.writeheader()
    writer.writerows(candidates)

print("LEXITECH TR - CHUNK SINIRI KALİTE KONTROLÜ")
print("-" * 60)

print(
    "Madde başlığıyla başlamayan devam chunk'ı:",
    len(candidates)
)

print("\nKANUN BAZINDA ADAY SAYILARI")

for law_number, count in sorted(counts.items()):
    print(law_number, ":", count)

print("\nİLK 10 İNCELEME ADAYI")
print("-" * 60)

for row in candidates[:10]:
    print(
        "\nKanun:",
        row["law_number"],
        "| Split:",
        row["split"]
    )
    print("Önceki:", row["previous_chunk"])
    print("Sonraki:", row["next_chunk"])
    print("ÖNCE:", row["previous_ends_with"])
    print("SONRA:", row["next_starts_with"])

print("\nRapor:", REPORT)
print("Chunk dosyaları değiştirilmedi.")

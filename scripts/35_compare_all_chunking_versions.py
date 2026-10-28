import hashlib
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("data/final/domain_v0.9")

VERSIONS = {
    "original": ROOT / "chunks",
    "sentence_aware": ROOT / "chunks_sentence_aware",
    "legal_aware": ROOT / "chunks_legal_aware",
}

SPLITS = ("train", "validation", "test")

REPORT = Path(
    "reports/quality/domain_chunk_final_comparison_v0.9.json"
)

ARTICLE_HEADING = re.compile(
    r"(?i)^(?:(?:mükerrer|ek|geçici)\s+)?"
    r"madde\s+\d+(?=[\s.\-–—]|$)"
)

LEGAL_NOTE = re.compile(
    r"(?i)^\((?:ek|değişik|mülga|"
    r"yeniden düzenlenen)\b"
)


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def sha256(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def inspect_version(directory):
    counts = Counter()
    problems = []
    word_examples = []

    for split in SPLITS:
        documents = read_jsonl(ROOT / f"{split}.jsonl")
        chunks = read_jsonl(directory / f"{split}.jsonl")

        counts["chunks"] += len(chunks)

        by_document = {}

        for chunk in chunks:
            by_document.setdefault(
                chunk["document_id"], []
            ).append(chunk)

            if chunk["split"] != split:
                problems.append("Split hatası: " + chunk["chunk_id"])

            if not 0 < chunk["token_count"] <= 2048:
                problems.append("Token sınırı: " + chunk["chunk_id"])

            if sha256(chunk["text"]) != chunk["text_sha256"]:
                problems.append("Chunk SHA: " + chunk["chunk_id"])

        for document in documents:
            doc_id = document["document_id"]

            pieces = sorted(
                by_document.pop(doc_id, []),
                key=lambda item: item["start_char"]
            )

            rebuilt = "".join(item["text"] for item in pieces)

            if rebuilt != document["text"]:
                problems.append("Metin bütünlüğü: " + doc_id)

            if sha256(rebuilt) != document["text_sha256"]:
                problems.append("Belge SHA: " + doc_id)

            position = 0

            for chunk in pieces:
                if chunk["start_char"] != position:
                    problems.append("Konum hatası: " + chunk["chunk_id"])

                position = chunk["end_char"]

            for previous, current in zip(pieces, pieces[1:]):
                if (
                    previous["section_type"] != "main_law"
                    or current["section_type"] != "main_law"
                ):
                    continue

                counts["main_law_boundaries"] += 1

                before = previous["text"]
                after = current["text"]

                # Metindeki gerçek iki komşu karaktere bak.
                if (
                    before
                    and after
                    and before[-1].isalpha()
                    and after[0].isalpha()
                ):
                    counts["inside_word"] += 1

                    if len(word_examples) < 5:
                        word_examples.append({
                            "law": str(current["law_number"]),
                            "before": before[-55:],
                            "after": after[:55],
                        })

                stripped_before = before.rstrip()
                stripped_after = after.lstrip()

                if ARTICLE_HEADING.match(stripped_after):
                    counts["article_heading"] += 1

                elif stripped_before.endswith((".", "!", "?")):
                    counts["possible_sentence_end"] += 1

                elif stripped_before.endswith((":", ";")):
                    counts["possible_clause_end"] += 1

                else:
                    counts["possible_mid_sentence"] += 1

                if LEGAL_NOTE.match(stripped_after):
                    counts["starts_with_legal_note"] += 1

                if re.search(
                    r"(?i)\((?:ek|değişik|mülga|"
                    r"yeniden düzenlenen)[^()\n]{0,120}\)\s*$",
                    stripped_before
                ):
                    counts["ends_with_legal_note"] += 1

        for unknown_doc in by_document:
            problems.append("Bilinmeyen belge: " + unknown_doc)

    return {
        "counts": dict(counts),
        "integrity_error_count": len(problems),
        "integrity_errors": problems[:10],
        "word_break_examples": word_examples,
    }


results = {
    name: inspect_version(directory)
    for name, directory in VERSIONS.items()
}

print("LEXITECH TR - ÜÇ CHUNKING SÜRÜMÜ KARŞILAŞTIRMASI")
print("=" * 65)

for name, result in results.items():
    c = result["counts"]

    print("\nSÜRÜM:", name)
    print("-" * 45)
    print("Toplam chunk:", c.get("chunks", 0))
    print("Kelime ortası bölünme:", c.get("inside_word", 0))
    print(
        "Olası cümle ortası:",
        c.get("possible_mid_sentence", 0)
    )
    print(
        "Olası cümle sonu:",
        c.get("possible_sentence_end", 0)
    )
    print(
        "Madde başlığında başlayan:",
        c.get("article_heading", 0)
    )
    print(
        "Hukuki notla başlayan chunk:",
        c.get("starts_with_legal_note", 0)
    )
    print(
        "Hukuki notla biten chunk:",
        c.get("ends_with_legal_note", 0)
    )
    print("Bütünlük hatası:", result["integrity_error_count"])

    for example in result["word_break_examples"][:3]:
        print(
            "  KELİME BÖLÜNMESİ:",
            example["law"],
            repr(example["before"]),
            "/",
            repr(example["after"])
        )

REPORT.parent.mkdir(parents=True, exist_ok=True)

REPORT.write_text(
    json.dumps(
        results,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("\nRapor:", REPORT)
print("Veri setlerinde hiçbir değişiklik yapılmadı.")
print("Cümle ve hukuki not ölçümleri ön değerlendirmedir.")

import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("data/final/domain_v0.9")
SPLITS = ("train", "validation", "test")

VERSIONS = {
    "old": ROOT / "chunks",
    "sentence_aware": ROOT / "chunks_sentence_aware"
}

REPORT = Path(
    "reports/quality/domain_chunk_comparison_v0.9.json"
)

HEADING = re.compile(
    r"(?i)^(?:(?:mükerrer|ek|geçici)\s+)?"
    r"madde\s+\d+(?=[\s.\-–—]|$)"
)

ABBREVIATION = re.compile(
    r"(?i)\b(?:md|bkz|vb|vs|dr|prof)\.$"
)


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def classify_boundary(previous, current):
    before = previous["text"].rstrip()
    after = current["text"].lstrip()

    if HEADING.match(after):
        return "article_heading"

    if before.endswith((".", "!", "?")):
        if ABBREVIATION.search(before):
            return "possible_mid_sentence"
        return "possible_sentence_end"

    if before.endswith((";", ":")):
        return "possible_clause_boundary"

    return "possible_mid_sentence"


def audit_version(directory):
    result = {
        "total_chunks": 0,
        "split_counts": {},
        "boundary_counts": Counter(),
        "mid_sentence_by_law": Counter(),
        "integrity_errors": [],
        "examples": []
    }

    for split in SPLITS:
        documents = load_jsonl(ROOT / f"{split}.jsonl")
        chunks = load_jsonl(directory / f"{split}.jsonl")

        result["split_counts"][split] = len(chunks)
        result["total_chunks"] += len(chunks)

        by_doc = {}

        for chunk in chunks:
            by_doc.setdefault(
                chunk["document_id"], []
            ).append(chunk)

        for doc in documents:
            pieces = sorted(
                by_doc.pop(doc["document_id"], []),
                key=lambda x: x["start_char"]
            )

            reconstructed = "".join(
                c["text"] for c in pieces
            )

            if reconstructed != doc["text"]:
                result["integrity_errors"].append(
                    doc["document_id"]
                )

            for current in pieces:
                if current["split"] != split:
                    result["integrity_errors"].append(
                        current["chunk_id"] + ": split"
                    )

                if not 0 < current["token_count"] <= 2048:
                    result["integrity_errors"].append(
                        current["chunk_id"] + ": token_limit"
                    )

            for previous, current in zip(
                pieces, pieces[1:]
            ):
                if (
                    previous["section_type"] != "main_law"
                    or current["section_type"] != "main_law"
                ):
                    continue

                category = classify_boundary(
                    previous, current
                )

                result["boundary_counts"][category] += 1

                if category == "possible_mid_sentence":
                    law = str(current["law_number"])
                    result["mid_sentence_by_law"][law] += 1

                    if len(result["examples"]) < 6:
                        result["examples"].append({
                            "law_number": law,
                            "before": previous["text"][-100:],
                            "after": current["text"][:100]
                        })

        for unknown in by_doc:
            result["integrity_errors"].append(
                "unknown_document:" + unknown
            )

    result["boundary_counts"] = dict(
        result["boundary_counts"]
    )
    result["mid_sentence_by_law"] = dict(
        sorted(result["mid_sentence_by_law"].items())
    )

    return result


results = {
    name: audit_version(path)
    for name, path in VERSIONS.items()
}

print("LEXITECH TR - CHUNKING SÜRÜMLERİ KARŞILAŞTIRMASI")
print("=" * 60)

for name, result in results.items():
    counts = result["boundary_counts"]

    print(f"\nSÜRÜM: {name}")
    print("-" * 45)
    print("Toplam chunk:", result["total_chunks"])
    print("Split dağılımı:", result["split_counts"])
    print(
        "Madde başlığında başlayan geçiş:",
        counts.get("article_heading", 0)
    )
    print(
        "Olası cümle sonu:",
        counts.get("possible_sentence_end", 0)
    )
    print(
        "Olası yan cümle/liste sınırı:",
        counts.get("possible_clause_boundary", 0)
    )
    print(
        "Olası cümle ortası:",
        counts.get("possible_mid_sentence", 0)
    )
    print(
        "Bütünlük hatası:",
        len(result["integrity_errors"])
    )

old = results["old"]["boundary_counts"].get(
    "possible_mid_sentence", 0
)
new = results["sentence_aware"]["boundary_counts"].get(
    "possible_mid_sentence", 0
)

print("\nKARŞILAŞTIRMA")
print("-" * 60)
print("Eski olası cümle ortası:", old)
print("Yeni olası cümle ortası:", new)
print("Değişim:", new - old)

if new < old:
    print("SONUÇ: Yeni sürüm bu ölçütte daha iyi.")
elif new == old:
    print("SONUÇ: Bu ölçütte iyileşme görülmedi.")
else:
    print("SONUÇ: Yeni sürüm bu ölçütte daha kötü.")

print("\nYENİ SÜRÜM - KANUN BAZINDA RİSKLER")
for law, count in results["sentence_aware"][
    "mid_sentence_by_law"
].items():
    print(law, ":", count)

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
print("Her iki chunk veri seti de değiştirilmedi.")
print(
    "Not: Cümle sınırı sınıflandırması "
    "sezgiseldir; manuel kontrol gerektirir."
)

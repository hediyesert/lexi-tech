import json
import re
from pathlib import Path
from collections import Counter

INPUT = Path("data/deduplicated/exact_unique.jsonl")
OUTPUT = Path(
    "data/interim/instruction_citation_review_v0.9.jsonl"
)
REPORT = Path(
    "reports/quality/instruction_citation_pool_v0.9.json"
)

LAW_PATTERNS = {
    "2709": [
        r"\b2709\s+sayılı\b",
        r"Türkiye Cumhuriyeti Anayasası",
        r"Anayasa(?:nın|'nın|’nın)\s+\d+\s*(?:inci|ıncı|uncu|üncü|\.)?\s*madd",
    ],
    "4721": [
        r"\b4721\s+sayılı\b",
        r"Türk Meden[îi] Kanunu",
        r"\bTMK\b",
    ],
    "6098": [
        r"\b6098\s+sayılı\b",
        r"Türk Borçlar Kanunu",
        r"\bTBK\b",
    ],
    "5237": [
        r"\b5237\s+sayılı\b",
        r"Türk Ceza Kanunu",
        r"\bTCK\b",
    ],
    "5271": [
        r"\b5271\s+sayılı\b",
        r"Ceza Muhakemesi Kanunu",
        r"\bCMK\b",
    ],
    "4857": [
        r"\b4857\s+sayılı\b",
        r"\bİş Kanunu\b",
    ],
    "6102": [
        r"\b6102\s+sayılı\b",
        r"Türk Ticaret Kanunu",
        r"\bTTK\b",
    ],
    "6502": [
        r"\b6502\s+sayılı\b",
        r"Tüketicinin Korunması Hakkında Kanun",
    ],
    "2577": [
        r"\b2577\s+sayılı\b",
        r"İdari Yargılama Usulü Kanunu",
        r"\bİYUK\b",
    ],
    "213": [
        r"\b213\s+sayılı\b",
        r"Vergi Usul Kanunu",
        r"\bVUK\b",
    ],
    "2004": [
        r"\b2004\s+sayılı\b",
        r"İcra ve İflas Kanunu",
        r"\bİİK\b",
    ],
    "5510": [
        r"\b5510\s+sayılı\b",
        r"Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu",
    ],
}

COMPILED = {
    law: [
        re.compile(pattern, re.IGNORECASE)
        for pattern in patterns
    ]
    for law, patterns in LAW_PATTERNS.items()
}

ARTICLE = re.compile(
    r"(?i)(?:"
    r"\bmadde\s+\d+"
    r"|\bmd\.?\s*\d+"
    r"|\bm\.\s*\d+"
    r"|\b\d+\s*(?:inci|ıncı|uncu|üncü)\s+madde"
    r"|\b\d+\.\s*madde"
    r")"
)

DRAFT = re.compile(
    r"(?i)\b(?:taslağ[ıia]|taslakta|taslak|"
    r"öngörülen|öngörülmektedir|kanun teklifi)\b"
)

CASE_LAW = re.compile(
    r"(?i)(?:Yargıtay|Danıştay|AİHM|"
    r"Anayasa Mahkemesi|\bAYM\b)"
)

counts = Counter()
by_law = Counter()
by_source = Counter()
examples = []

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

with INPUT.open(encoding="utf-8") as source_file, \
     OUTPUT.open("w", encoding="utf-8") as output_file:

    for line in source_file:
        if not line.strip():
            continue

        record = json.loads(line)
        counts["total"] += 1

        question = str(record.get("question") or "").strip()
        answer = str(record.get("answer") or "").strip()
        combined = question + "\n" + answer

        laws = [
            number
            for number, patterns in COMPILED.items()
            if any(p.search(combined) for p in patterns)
        ]

        has_article = bool(ARTICLE.search(answer))
        has_draft = bool(DRAFT.search(combined))
        has_case_law = bool(CASE_LAW.search(combined))

        if not laws:
            counts["no_target_law_indicator"] += 1
        elif len(laws) > 1:
            counts["multiple_target_laws"] += 1
        else:
            counts["single_target_law"] += 1

        if not has_article:
            counts["answer_without_article_indicator"] += 1

        if has_draft:
            counts["draft_indicator"] += 1

        if has_case_law:
            counts["case_law_indicator"] += 1

        eligible = (
            len(laws) == 1
            and has_article
            and not has_draft
            and len(question) >= 15
            and len(answer) >= 30
        )

        if not eligible:
            continue

        law = laws[0]
        counts["review_candidates"] += 1
        by_law[law] += 1
        by_source[str(record.get("source"))] += 1

        candidate = {
            "id": record.get("id"),
            "question": question,
            "answer": answer,
            "source": record.get("source"),
            "source_document": record.get("source_document"),
            "law_indicator": law,
            "has_answer_article_indicator": True,
            "has_case_law_indicator": has_case_law,
            "legal_reference_verified": False,
            "human_review_status": "pending",
            "rights_status": "pending_review",
            "selection_method": "heuristic_v0.9",
        }

        output_file.write(
            json.dumps(candidate, ensure_ascii=False) + "\n"
        )

        if len(examples) < 5:
            examples.append({
                "law": law,
                "question": question[:170],
                "answer": answer[:230],
                "source_document": record.get("source_document"),
            })

report = {
    "counts": dict(counts),
    "review_candidates_by_law": dict(by_law),
    "review_candidates_by_source": dict(by_source),
    "examples": examples,
    "warning": (
        "This is a heuristic review pool, not a legally "
        "verified or training-approved instruction dataset."
    ),
}

REPORT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("LEXITECH TR - INSTRUCTION DOĞRULAMA HAVUZU")
print("=" * 60)
print("İncelenen kayıt:", counts["total"])
print("Tek kanun göstergesi:", counts["single_target_law"])
print("Birden fazla kanun göstergesi:", counts["multiple_target_laws"])
print("Taslak göstergesi:", counts["draft_indicator"])
print("Karar içeriği göstergesi:", counts["case_law_indicator"])
print("Doğrulama havuzuna alınan:", counts["review_candidates"])

print("\nKANUN BAZINDA ADAYLAR")
for law, count in sorted(by_law.items()):
    print(f"  {law}: {count:,}")

print("\nKAYNAK BAZINDA ADAYLAR")
for source, count in by_source.items():
    print(f"  {source}: {count:,}")

print("\nİLK 5 ÖRNEK")
for item in examples:
    print("\nKanun:", item["law"])
    print("Soru:", item["question"])
    print("Cevap:", item["answer"])

print("\nAday dosyası:", OUTPUT)
print("Rapor:", REPORT)
print("Hukuki doğruluk ve kullanım hakları henüz onaylanmadı.")
print("Orijinal 308.009 kayıt değiştirilmedi.")

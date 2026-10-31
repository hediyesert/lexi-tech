import csv
import json
import re
from collections import Counter
from itertools import zip_longest
from pathlib import Path

POOL = Path(
    "data/interim/instruction_citation_review_v0.9.jsonl"
)

AUDIT = Path(
    "data/interim/instruction_article_audit_v0.9.jsonl"
)

OUTPUT = Path(
    "reports/quality/instruction_reference_mismatches_v0.9.csv"
)

LAW_INDICATORS = {
    "2709": [r"\b2709\s+sayılı", r"Türkiye Cumhuriyeti Anayasası"],
    "4721": [r"\b4721\s+sayılı", r"\bTMK\b", r"Türk Meden[îi] Kanunu"],
    "6098": [r"\b6098\s+sayılı", r"\bTBK\b", r"Türk Borçlar Kanunu"],
    "5237": [r"\b5237\s+sayılı", r"\bTCK\b", r"Türk Ceza Kanunu"],
    "5271": [r"\b5271\s+sayılı", r"\bCMK\b", r"Ceza Muhakemesi Kanunu"],
    "4857": [r"\b4857\s+sayılı", r"\bİş Kanunu\b"],
    "6102": [r"\b6102\s+sayılı", r"\bTTK\b", r"Türk Ticaret Kanunu"],
    "6502": [r"\b6502\s+sayılı", r"Tüketicinin Korunması Hakkında Kanun"],
    "2577": [r"\b2577\s+sayılı", r"\bİYUK\b", r"İdari Yargılama Usulü Kanunu"],
    "213": [r"\b213\s+sayılı", r"\bVUK\b", r"Vergi Usul Kanunu"],
    "2004": [r"\b2004\s+sayılı", r"\bİİK\b", r"İcra ve İflas Kanunu"],
    "5510": [r"\b5510\s+sayılı", r"Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu"],
}

compiled = {
    law: [re.compile(p, re.IGNORECASE) for p in patterns]
    for law, patterns in LAW_INDICATORS.items()
}

def read_records(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

rows = []
by_law = Counter()
missing_numbers = Counter()
other_law_indicators = Counter()

for candidate, audit in zip_longest(
    read_records(POOL),
    read_records(AUDIT)
):
    if candidate is None or audit is None:
        raise ValueError("İki dosyanın kayıt sayıları farklı.")

    if str(candidate["id"]) != str(audit["id"]):
        raise ValueError("Kayıt sırası uyuşmuyor.")

    if audit["structural_status"] != "requires_reference_review":
        continue

    assigned_law = str(candidate["law_indicator"])

    text = (
        candidate["question"] + "\n" +
        candidate["answer"]
    )

    explicit_laws = sorted(
        law
        for law, patterns in compiled.items()
        if any(pattern.search(text) for pattern in patterns)
    )

    alternative_indicators = [
        law for law in explicit_laws
        if law != assigned_law
    ]

    numbers_not_found = audit["numbers_not_found_in_target_law"]

    by_law[assigned_law] += 1
    missing_numbers.update(
        str(number) for number in numbers_not_found
    )

    for law in alternative_indicators:
        other_law_indicators[law] += 1

    rows.append({
        "id": candidate["id"],
        "assigned_law": assigned_law,
        "source": candidate["source"],
        "source_document": candidate["source_document"] or "",
        "extracted_article_numbers": ",".join(
            map(str, audit["referenced_article_numbers"])
        ),
        "numbers_not_found": ",".join(
            map(str, numbers_not_found)
        ),
        "explicit_law_indicators": ",".join(explicit_laws),
        "other_law_indicators": ",".join(
            alternative_indicators
        ),
        "question": candidate["question"],
        "answer": candidate["answer"],
        "review_status": "pending",
        "review_notes": ""
    })

if len(rows) != 933:
    raise ValueError(
        f"933 şüpheli kayıt bekleniyordu, {len(rows)} bulundu."
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

print("LEXITECH TR - ŞÜPHELİ KANUN ATIFLARI")
print("=" * 60)
print("İncelenecek kayıt:", len(rows))
print("Rapor:", OUTPUT)

print("\nKANUN BAZINDA")
for law, count in sorted(by_law.items()):
    print(f"  {law}: {count}")

print("\nEN SIK BULUNAMAYAN MADDE NUMARALARI")
for number, count in missing_numbers.most_common(15):
    print(f"  Madde {number}: {count}")

print("\nDİĞER KANUN GÖSTERGELERİ")
for law, count in other_law_indicators.most_common():
    print(f"  {law}: {count}")

print("\nİLK 10 ŞÜPHELİ KAYIT")
print("-" * 60)

for index, row in enumerate(rows[:10], 1):
    print(f"\n[{index}] Etiket: {row['assigned_law']}")
    print("Bulunamayan madde:", row["numbers_not_found"])
    print("Diğer kanun göstergesi:", row["other_law_indicators"])
    print("SORU:", row["question"][:400])
    print("CEVAP:", row["answer"][:650])

print("\nKanun etiketleri otomatik değiştirilmedi.")
print("Hukuki doğruluk onayı verilmedi.")

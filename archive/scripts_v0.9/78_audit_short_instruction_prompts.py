import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

CANDIDATES = Path(
    "data/interim/instruction_quality_candidates_v0.9.csv"
)

DATA = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)

# Soru işareti olmadan da geçerli görev bildiren
# yaygın Türkçe talimat sonları.
TASK_ENDINGS = re.compile(
    r"(?:"
    r"sayınız|sayın|"
    r"açıklayınız|açıklayın|"
    r"belirtiniz|belirtin|"
    r"yazınız|yazın|"
    r"sıralayınız|sıralayın|"
    r"tanımlayınız|tanımlayın|"
    r"karşılaştırınız|karşılaştırın|"
    r"değerlendiriniz|değerlendirin|"
    r"tartışınız|tartışın|"
    r"anlatınız|anlatın|"
    r"inceleyiniz|inceleyin|"
    r"listeleyiniz|listeleyin|"
    r"özetleyiniz|özetleyin|"
    r"gösteriniz|gösterin|"
    r"veriniz|verin|"
    r"izah ediniz|izah edin"
    r")\s*[.!…]*\s*$",
    re.IGNORECASE,
)

with CANDIDATES.open(encoding="utf-8-sig", newline="") as f:
    candidate_rows = list(csv.DictReader(f))

selected = {
    row["record_id"]: row
    for row in candidate_rows
    if "short_question_without_question_mark"
    in row["quality_signals"].split("|")
}

if len(selected) != 268:
    raise ValueError(
        f"268 kısa metin bekleniyordu: {len(selected)}"
    )

records = {}

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            rid = record["id"]

            if rid in selected:
                records[rid] = (
                    split,
                    record["messages"][0]["content"]
                )

if set(records) != set(selected):
    raise ValueError("Bazı kısa metin kayıtları bulunamadı.")

groups = {
    "explicit_instruction": [],
    "needs_content_review": [],
}

for rid, (split, question) in records.items():
    if TASK_ENDINGS.search(question.strip()):
        group = "explicit_instruction"
    else:
        group = "needs_content_review"

    groups[group].append({
        "id": rid,
        "split": split,
        "question": question,
    })

def stable_order(item):
    return hashlib.sha256(
        item["id"].encode("utf-8")
    ).hexdigest()

print("LEXITECH TR - KISA TALIMAT KALITE ANALIZI")
print("=" * 65)
print("Toplam incelenen:", len(selected))

for group, label in (
    ("explicit_instruction", "ACIK TALIMAT ICEREN"),
    ("needs_content_review", "ICERIK INCELEMESI GEREKEN"),
):
    items = sorted(groups[group], key=stable_order)

    print("\n" + "=" * 65)
    print(label)
    print("Kayit sayisi:", len(items))
    print("Split dagilimi:",
          dict(Counter(x["split"] for x in items)))

    limit = 5 if group == "explicit_instruction" else 20

    for index, item in enumerate(items[:limit], 1):
        print(f"\nORNEK {index}")
        print("Split:", item["split"])
        print("Kayit ID:", item["id"][:16])
        print(
            "METIN:",
            item["question"][:220].replace("\n", " ")
        )

print("\nNOT:")
print("Acik talimat eslesmesi otomatik bir sezgisel kontroldur.")
print("Eslesmeyen kayitlar otomatik olarak hatali sayilmaz.")
print("Hicbir dosya degistirilmedi.")

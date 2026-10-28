import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

POOL = Path(
    "data/interim/instruction_citation_review_v0.9.jsonl"
)
AUDIT = Path(
    "data/interim/instruction_article_audit_v0.9.jsonl"
)
REPORT = Path(
    "reports/splits/instruction_split_plan_v0.9.json"
)

def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def normalize_question(text):
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().casefold()

parent = {}

def find(x):
    parent.setdefault(x, x)
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[max(ra, rb)] = min(ra, rb)

counts = Counter()
document_counts = Counter()
question_owner = {}

print("LEXITECH TR - INSTRUCTION SPLIT PLANI")
print("=" * 60)

# İlk geçiş: belge ve aynı soru ilişkilerini belirle.
pool_iter = read_jsonl(POOL)
audit_iter = read_jsonl(AUDIT)

from itertools import zip_longest

for candidate, audit in zip_longest(
    pool_iter, audit_iter
):
    if candidate is None or audit is None:
        raise ValueError("Havuz ve denetim uzunlukları farklı.")

    if str(candidate["id"]) != str(audit["id"]):
        raise ValueError("Kayıt ID eşleşmesi bozuk.")

    counts["all_candidates"] += 1

    if audit["structural_status"] != "numbers_present_in_target_law":
        counts["reference_review_quarantine"] += 1
        continue

    if candidate["source"] == "OrionCAF/turkish_law_qa_dataset":
        counts["missing_source_quarantine"] += 1
        continue

    doc = candidate.get("source_document")

    if not doc:
        counts["other_missing_source_quarantine"] += 1
        continue

    doc = str(doc)
    find(doc)

    counts["provisional_candidates"] += 1
    document_counts[doc] += 1

    question = normalize_question(candidate["question"])

    if question in question_owner:
        other_doc = question_owner[question]

        if find(doc) != find(other_doc):
            union(doc, other_doc)
            counts["cross_document_question_links"] += 1
    else:
        question_owner[question] = doc

groups = Counter()

for doc, count in document_counts.items():
    groups[find(doc)] += count

# En büyük grupları önce yerleştir.
# Aynı soru nedeniyle birleşen dosyalar ayrılmaz.
targets = {
    "train": counts["provisional_candidates"] * 0.90,
    "validation": counts["provisional_candidates"] * 0.05,
    "test": counts["provisional_candidates"] * 0.05,
}

sizes = Counter()
group_splits = {}

ordered_groups = sorted(
    groups.items(),
    key=lambda item: (
        -item[1],
        hashlib.sha256(
            item[0].encode("utf-8")
        ).hexdigest()
    )
)

for group, size in ordered_groups:
    def score(split):
        proposed = sizes.copy()
        proposed[split] += size

        return sum(
            abs(proposed[s] - targets[s])
            for s in targets
        )

    chosen = min(
        ("train", "validation", "test"),
        key=lambda split: (
            score(split),
            ("train", "validation", "test").index(split)
        )
    )

    group_splits[group] = chosen
    sizes[chosen] += size

document_splits = {
    doc: group_splits[find(doc)]
    for doc in document_counts
}

if len(set(document_splits.values())) != 3:
    raise ValueError(
        "Üç ayrı veri kümesi oluşmadı. "
        "Kaynak dosyası ilişkileri incelenmeli."
    )

# Planı kaydetmeden önce toplamsal kontrol.
if sum(sizes.values()) != counts["provisional_candidates"]:
    raise ValueError("Kayıt sayısı uyuşmuyor.")

report = {
    "version": "v0.9",
    "status": "provisional_not_training_approved",
    "method": (
        "source_document_grouped_and_"
        "identical_question_connected"
    ),
    "counts": dict(counts),
    "source_document_count": len(document_counts),
    "connected_document_group_count": len(groups),
    "largest_connected_group": max(groups.values()),
    "split_counts": dict(sizes),
    "split_targets": targets,
    "document_splits": document_splits,
    "limitations": [
        "Hukuki doğruluk henüz doğrulanmadı.",
        "Kaynak kullanım hakları inceleniyor.",
        "Yakın anlamlı soru tekrarları henüz giderilmedi.",
        "Kanun eşleştirmeleri sezgiseldir.",
        "Bu plan eğitim için nihai onay değildir."
    ]
}

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Toplam doğrulama adayı:", counts["all_candidates"])
print(
    "Şüpheli atıf nedeniyle ayrılan:",
    counts["reference_review_quarantine"]
)
print(
    "OrionCAF nedeniyle ayrılan:",
    counts["missing_source_quarantine"]
)
print(
    "Diğer kaynak eksikliği:",
    counts["other_missing_source_quarantine"]
)
print(
    "Ön taslak için kalan:",
    counts["provisional_candidates"]
)
print("Farklı kaynak dosyası:", len(document_counts))
print(
    "Birbirine bağlı belge grubu:",
    len(groups)
)
print(
    "En büyük bağlantılı grup:",
    max(groups.values())
)

print("\nBELGE BAZLI SPLIT DAĞILIMI")
for split in ("train", "validation", "test"):
    print(f"  {split}: {sizes[split]:,}")

print("\nRapor:", REPORT)
print("Henüz eğitim JSONL dosyaları oluşturulmadı.")
print("Mevcut veri setleri değiştirilmedi.")

import csv
import json
from collections import Counter
from pathlib import Path

DATA = Path("data/interim/instruction_leakage_clean_v0.9")
QUARANTINE = Path(
    "data/interim/instruction_quality_quarantine_v0.9.csv"
)
OUTPUT = Path(
    "data/interim/instruction_headline_review_13_v0.9.csv"
)

if OUTPUT.exists():
    raise SystemExit("Çıktı zaten mevcut; üzerine yazılmadı.")

# Adım 344'te görülen 13 kayıt.
# 'statement': önerme cümlesi
# 'headline': başlık / konu ifadesi
CLASSIFICATIONS = {
    "0305f6155d3585f4": "headline",
    "1de29319684a36cc": "statement",
    "2d126cb2f49a20dd": "headline",
    "3c54dde57b1e426a": "headline",
    "4d49869b98a0cf75": "statement",
    "4e5ec1c387c24ff": "headline",
    "5d0c850aae1377af": "headline",
    "805236d6b95f5327": "headline",
    "85f196e605f1041a": "headline",
    "b8301600a6d506a9": "headline",
    "bf50d64b3d3c50c3": "headline",
    "c8f74c3088ff9d80": "headline",
    "ec5c4ff997f67055": "headline",
}

with QUARANTINE.open(encoding="utf-8-sig", newline="") as f:
    quarantined_ids = {
        row["record_id"]
        for row in csv.DictReader(f)
    }

found = {}

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            record_id = record["id"]

            for prefix in CLASSIFICATIONS:
                if record_id.startswith(prefix):
                    if prefix in found:
                        raise ValueError(
                            "Bir ID başlangıcı birden fazla kayıtla eşleşti."
                        )
                    found[prefix] = (split, record)

if set(found) != set(CLASSIFICATIONS):
    raise ValueError("13 kaydın tamamı bulunamadı.")

queue = []

for prefix, prompt_form in CLASSIFICATIONS.items():
    split, record = found[prefix]

    if split != "train":
        raise ValueError("Bu gruptaki tüm kayıtlar train olmalı.")

    question = record["messages"][0]["content"]
    answer = record["messages"][1]["content"]

    queue.append({
        "record_id": record["id"],
        "split": split,
        "question_text": question,
        "prompt_form": prompt_form,
        "answer_length": len(answer),
        "existing_quarantine": (
            "yes" if record["id"] in quarantined_ids else "no"
        ),
        "review_status": "assistant_preliminary",
        "recommended_action": (
            "review_prompt_format_and_source_before_training"
        ),
        "legal_accuracy_review": "required",
        "source_provenance_review": "required",
        "personal_data_review": "required",
        "final_human_decision": "",
        "notes": (
            "Baslik veya onerme niteliginde. "
            "Otomatik silme veya yeniden yazma yapilmadi."
        ),
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(queue[0].keys())
    )
    writer.writeheader()
    writer.writerows(queue)

forms = Counter(row["prompt_form"] for row in queue)
already = sum(
    row["existing_quarantine"] == "yes"
    for row in queue
)

print("LEXITECH TR - BASLIK FORMATLI INSTRUCTION INCELEMESI")
print("=" * 60)
print("Toplam kayit:", len(queue))
print("Baslik / konu ifadesi:", forms["headline"])
print("Onerme cumlesi:", forms["statement"])
print("Zaten karantinada olan:", already)
print("Yeni bicim inceleme adayi:", len(queue) - already)
print("Nihai insan karari: 0")
print("\nInceleme listesi:", OUTPUT)
print("Kayit silinmedi veya yeniden yazilmadi.")
print("Ana veri setleri degistirilmedi.")

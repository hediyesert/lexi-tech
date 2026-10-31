import csv
from collections import Counter
from pathlib import Path

BASE = Path("data/interim")

QUARANTINE = (
    BASE / "instruction_quality_quarantine_v0.9.csv"
)
HEADLINES = (
    BASE / "instruction_headline_review_13_v0.9.csv"
)
OUTPUT = (
    BASE / "instruction_quality_decision_queue_14_v0.9.csv"
)

if OUTPUT.exists():
    raise SystemExit(
        "Birleştirilmiş liste zaten mevcut; üzerine yazılmadı."
    )

def read_csv(path):
    with path.open(
        encoding="utf-8-sig", newline=""
    ) as f:
        return list(csv.DictReader(f))

old_rows = read_csv(QUARANTINE)
headline_rows = read_csv(HEADLINES)

if len(old_rows) != 2:
    raise ValueError("İlk listede 2 kayıt bekleniyordu.")

if len(headline_rows) != 13:
    raise ValueError("Başlık listesinde 13 kayıt bekleniyordu.")

merged = {}

for row in old_rows:
    rid = row["record_id"]

    if rid in merged:
        raise ValueError("İlk listede tekrarlı ID bulundu.")

    merged[rid] = {
        "record_id": rid,
        "split": row["split"],
        "quality_reasons": [row["quality_flag"]],
        "affected_fields": [row["affected_field"]],
        "prompt_form": "",
    }

for row in headline_rows:
    rid = row["record_id"]
    form = row["prompt_form"]

    if form not in ("headline", "statement"):
        raise ValueError("Beklenmeyen prompt biçimi.")

    reason = (
        "headline_prompt"
        if form == "headline"
        else "statement_prompt"
    )

    if rid not in merged:
        merged[rid] = {
            "record_id": rid,
            "split": row["split"],
            "quality_reasons": [],
            "affected_fields": [],
            "prompt_form": "",
        }

    item = merged[rid]

    if item["split"] != row["split"]:
        raise ValueError("Split bilgileri uyuşmuyor.")

    item["quality_reasons"].append(reason)
    item["affected_fields"].append("question")
    item["prompt_form"] = form

if len(merged) != 14:
    raise ValueError(
        f"14 benzersiz kayıt bekleniyordu: {len(merged)}"
    )

result = []

for rid, item in sorted(merged.items()):
    reasons = sorted(set(item["quality_reasons"]))
    fields = sorted(set(item["affected_fields"]))

    if "citation_only_answer" in reasons:
        possible_action = (
            "verify_answer_sufficiency_and_source"
        )
    elif item["prompt_form"] == "headline":
        possible_action = (
            "review_reframing_or_dataset_reclassification"
        )
    elif item["prompt_form"] == "statement":
        possible_action = (
            "verify_legal_claim_and_review_reframing"
        )
    else:
        possible_action = (
            "review_prompt_format_and_source"
        )

    result.append({
        "record_id": rid,
        "split": item["split"],
        "affected_fields": "|".join(fields),
        "quality_reasons": "|".join(reasons),
        "prompt_form": item["prompt_form"],
        "review_status": "assistant_preliminary",
        "recommended_treatment": (
            "hold_from_future_training_pending_review"
        ),
        "possible_next_action": possible_action,
        "legal_accuracy_review": "required",
        "source_and_rights_review": "required",
        "personal_data_screening": "required",
        "final_human_decision": "",
        "decision_notes": "",
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(result[0].keys())
    )
    writer.writeheader()
    writer.writerows(result)

reasons = Counter(
    reason
    for item in result
    for reason in item["quality_reasons"].split("|")
)

print("LEXITECH TR - BIRLESIK KALITE KARAR LISTESI")
print("=" * 60)

print("Ilk karantina listesi:", len(old_rows))
print("Baslik inceleme listesi:", len(headline_rows))
print("Benzersiz inceleme kaydi:", len(result))

print("\nKALITE GEREKCELERI")
for reason, count in sorted(reasons.items()):
    print(f"{reason}: {count}")

print("\nGecici bekletme onerisi:", len(result))
print("Nihai insan karari: 0")
print("Egitim onayi verilen: 0")

print("\nYeni liste:", OUTPUT)
print("Ana veri setleri degistirilmedi.")
print("Kayit silinmedi veya yeniden yazilmadi.")
print("Fiziksel egitim filtresi henuz uygulanmadi.")

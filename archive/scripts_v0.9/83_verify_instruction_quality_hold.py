import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

BASE = Path("data/interim")
DATA = BASE / "instruction_leakage_clean_v0.9"
QUEUE = BASE / "instruction_quality_decision_queue_14_v0.9.csv"
MANIFEST = BASE / "instruction_quality_hold_manifest_v0.9.json"

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

if manifest.get("purpose") != "instruction_quality_hold":
    raise ValueError("Beklenmeyen manifesto türü.")

if manifest.get("training_approved") is not False:
    raise ValueError("Manifestonun eğitim onayı güvenli değil.")

if manifest.get("actual_records_removed") != 0:
    raise ValueError("Manifestodaki çıkarma durumu beklenmiyor.")

actual_hash = hashlib.sha256(QUEUE.read_bytes()).hexdigest()

if actual_hash != manifest["source_review_sha256"]:
    raise ValueError(
        "Kaynak karar listesi değişmiş! "
        "Manifesto yeniden incelenmeli."
    )

with QUEUE.open(encoding="utf-8-sig", newline="") as f:
    queue = list(csv.DictReader(f))

if len(queue) != 14:
    raise ValueError("Karar listesinde 14 kayıt bekleniyor.")

hold_ids = {row["record_id"] for row in queue}

if len(hold_ids) != 14:
    raise ValueError("Tekrarlı karar listesi ID'si.")

if any(row["final_human_decision"].strip() for row in queue):
    raise ValueError("İnsan kararı değişmiş; yeniden değerlendirin.")

manifest_records = manifest["hold_records"]

if len(manifest_records) != 14:
    raise ValueError("Manifestoda 14 kayıt bekleniyor.")

if {row["record_id"] for row in manifest_records} != hold_ids:
    raise ValueError("Manifesto ve karar listesi uyuşmuyor.")

manifest_by_id = {
    row["record_id"]: row for row in manifest_records
}

queue_by_id = {row["record_id"]: row for row in queue}

for rid in hold_ids:
    q = queue_by_id[rid]
    m = manifest_by_id[rid]

    if q["split"] != m["split"]:
        raise ValueError("Kayıt split bilgisi uyuşmuyor.")

    if sorted(q["quality_reasons"].split("|")) != sorted(
        m["quality_reasons"]
    ):
        raise ValueError("Kayıt kalite gerekçeleri uyuşmuyor.")

    if m["decision_status"] != "pending_human_review":
        raise ValueError("Beklenmeyen insan inceleme durumu.")

counts = Counter()
held = Counter()
found = set()

for split in ("train", "validation", "test"):
    path = DATA / f"{split}.jsonl"

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            rid = record["id"]
            counts[split] += 1

            if rid in hold_ids:
                if rid in found:
                    raise ValueError("Bekletilen ID tekrar ediyor.")

                if queue_by_id[rid]["split"] != split:
                    raise ValueError("Gerçek split bilgisi uyuşmuyor.")

                found.add(rid)
                held[split] += 1

if found != hold_ids:
    raise ValueError(
        f"Eksik bekletme kaydı: {len(hold_ids - found)}"
    )

for split in ("train", "validation", "test"):
    original = counts[split]
    excluded = held[split]
    remaining = original - excluded

    if original != manifest["original_split_counts"][split]:
        raise ValueError(f"{split}: başlangıç sayısı değişmiş.")

    if excluded != manifest["held_split_counts"][split]:
        raise ValueError(f"{split}: bekletme sayısı uyuşmuyor.")

    if remaining != manifest["proposed_remaining_split_counts"][split]:
        raise ValueError(f"{split}: kalan sayı uyuşmuyor.")

if sum(counts.values()) != 124510:
    raise ValueError("Toplam QA sayısı değişmiş.")

print("LEXITECH TR - KALITE FILTRESI ON KONTROLU")
print("=" * 60)
print("Manifesto SHA-256 kontrolu: BASARILI")
print("Manifesto / karar listesi uyumu: BASARILI")
print("Bekletilecek benzersiz QA:", len(hold_ids))

for split in ("train", "validation", "test"):
    print(
        f"{split}: mevcut={counts[split]}, "
        f"bekletilecek={held[split]}, "
        f"olasi_kalan={counts[split] - held[split]}"
    )

print("\nToplam mevcut:", sum(counts.values()))
print("Bekletme sonrasi olasi:", sum(counts.values()) - len(hold_ids))
print("Egitim onayi: YOK")
print("Kontrol sonucu: BASARILI")
print("Mod: DRY-RUN")
print("Dosyadan cikarilan kayit: 0")
print("Ana veri setleri degistirilmedi.")

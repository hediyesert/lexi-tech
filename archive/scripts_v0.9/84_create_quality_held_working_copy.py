import csv
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path

BASE = Path("data/interim")

SOURCE = BASE / "instruction_leakage_clean_v0.9"

QUEUE = BASE / "instruction_quality_decision_queue_14_v0.9.csv"

MANIFEST = BASE / "instruction_quality_hold_manifest_v0.9.json"

OUTPUT = BASE / "instruction_quality_held_working_v0.9"

SPLITS = ("train", "validation", "test")

if OUTPUT.exists():
    raise SystemExit(
        "Çıktı klasörü zaten mevcut. Üzerine yazılmadı: "
        + str(OUTPUT)
    )

manifest = json.loads(
    MANIFEST.read_text(encoding="utf-8")
)

if manifest.get("purpose") != "instruction_quality_hold":
    raise ValueError("Yanlış manifesto türü.")

if manifest.get("training_approved") is not False:
    raise ValueError("Eğitim onayı güvenlik kontrolü başarısız.")

if manifest.get("actual_records_removed") != 0:
    raise ValueError("Manifestonun başlangıç durumu beklenmiyor.")

queue_hash = hashlib.sha256(
    QUEUE.read_bytes()
).hexdigest()

if queue_hash != manifest["source_review_sha256"]:
    raise ValueError(
        "Karar listesi değişmiş. Manifesto yeniden incelenmeli."
    )

with QUEUE.open(encoding="utf-8-sig", newline="") as f:
    queue = list(csv.DictReader(f))

if len(queue) != 14:
    raise ValueError("14 karar kaydı bekleniyordu.")

hold_ids = {row["record_id"] for row in queue}

if len(hold_ids) != 14:
    raise ValueError("Tekrarlı bekletme ID'si.")

manifest_records = manifest["hold_records"]

if len(manifest_records) != 14:
    raise ValueError("Manifestoda 14 kayıt bekleniyordu.")

manifest_by_id = {
    item["record_id"]: item
    for item in manifest_records
}

if len(manifest_by_id) != 14:
    raise ValueError("Manifestoda tekrarlı kayıt var.")

if set(manifest_by_id) != hold_ids:
    raise ValueError("Manifesto ve karar listesi uyuşmuyor.")

for row in queue:
    rid = row["record_id"]
    item = manifest_by_id[rid]

    if row["split"] != item["split"]:
        raise ValueError("Split bilgisi uyuşmuyor.")

    if row["recommended_treatment"] != (
        "hold_from_future_training_pending_review"
    ):
        raise ValueError("Beklenmeyen bekletme kararı.")

    if row["final_human_decision"].strip():
        raise ValueError(
            "İnsan kararı değişmiş. Önce manifesto güncellenmeli."
        )

    if item["decision_status"] != "pending_human_review":
        raise ValueError("Manifesto karar durumu değişmiş.")

    if sorted(row["quality_reasons"].split("|")) != sorted(
        item["quality_reasons"]
    ):
        raise ValueError("Kalite gerekçeleri uyuşmuyor.")

counts = Counter()
held = Counter()
written = Counter()
found_held = set()

BASE.mkdir(parents=True, exist_ok=True)

temporary = Path(
    tempfile.mkdtemp(
        prefix=".quality_held_working_tmp_",
        dir=BASE,
    )
)

try:
    for split in SPLITS:
        source_file = SOURCE / f"{split}.jsonl"
        output_file = temporary / f"{split}.jsonl"

        with (
            source_file.open(encoding="utf-8") as src,
            output_file.open("w", encoding="utf-8") as dst
        ):
            for line in src:
                if not line.strip():
                    continue

                record = json.loads(line)
                rid = record["id"]

                counts[split] += 1

                if rid in hold_ids:
                    if rid in found_held:
                        raise ValueError(
                            "Bekletilen kayıt birden fazla kez bulundu."
                        )

                    if manifest_by_id[rid]["split"] != split:
                        raise ValueError(
                            "Kayıt gerçek split bilgisiyle uyuşmuyor."
                        )

                    found_held.add(rid)
                    held[split] += 1
                    continue

                # Orijinal JSONL satırını değiştirmeden aktar.
                dst.write(line if line.endswith("\n") else line + "\n")
                written[split] += 1

    if found_held != hold_ids:
        raise ValueError(
            f"Eksik bekletme kaydı: {len(hold_ids - found_held)}"
        )

    for split in SPLITS:
        if counts[split] != manifest["original_split_counts"][split]:
            raise ValueError(
                f"{split}: orijinal kayıt sayısı uyuşmuyor."
            )

        if held[split] != manifest["held_split_counts"][split]:
            raise ValueError(
                f"{split}: bekletme sayısı uyuşmuyor."
            )

        expected = manifest[
            "proposed_remaining_split_counts"
        ][split]

        if written[split] != expected:
            raise ValueError(
                f"{split}: çıktı sayısı beklenenden farklı."
            )

        if counts[split] != held[split] + written[split]:
            raise ValueError(
                f"{split}: kayıt dengesi bozuk."
            )

    if sum(counts.values()) != 124510:
        raise ValueError("Kaynak veri toplamı beklenenden farklı.")

    if sum(written.values()) != 124496:
        raise ValueError("Çıktı toplamı beklenenden farklı.")

    audit = {
        "project": "LexiTech TR",
        "version": "v0.9",
        "output_type": "interim_quality_held_working_copy",
        "status": "preliminary_not_training_approved",
        "source_directory": str(SOURCE),
        "manifest_file": str(MANIFEST),
        "source_queue_sha256": queue_hash,
        "original_counts": dict(counts),
        "held_counts": {
            split: held[split] for split in SPLITS
        },
        "output_counts": {
            split: written[split] for split in SPLITS
        },
        "total_original": 124510,
        "total_held": 14,
        "total_output": 124496,
        "training_approved": False,
        "rights_status": "pending_review",
        "independent_human_approval": False,
        "limitations": [
            "Only 14 preliminarily held records were excluded.",
            "Other quality candidates remain under review.",
            "Legal accuracy and provenance are not fully verified.",
            "Training rights and licensing are unresolved.",
        ],
    }

    (temporary / "quality_hold_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Tüm kontroller başarılı olduktan sonra
    # geçici klasörü nihai konuma taşı.
    if OUTPUT.exists():
        raise ValueError("Çıktı klasörü işlem sırasında oluştu.")

    os.replace(temporary, OUTPUT)

except Exception:
    if temporary.exists():
        shutil.rmtree(temporary)
    raise

print("LEXITECH TR - KALITE FILTRELI CALISMA KOPYASI")
print("=" * 60)

for split in SPLITS:
    print(
        f"{split}: "
        f"kaynak={counts[split]}, "
        f"bekletilen={held[split]}, "
        f"kopyada={written[split]}"
    )

print("\nToplam kaynak QA:", sum(counts.values()))
print("Calisma kopyasinda bekletilen:", sum(held.values()))
print("Calisma kopyasi QA:", sum(written.values()))

print("\nCikti klasoru:", OUTPUT)
print("Denetim raporu:", OUTPUT / "quality_hold_audit.json")

print("\nEgitim onayi: HAYIR")
print("Kaynak haklari: INCELEME BEKLIYOR")
print("Orijinal veri setleri: DEGISTIRILMEDI")
print("Islem: BASARILI")

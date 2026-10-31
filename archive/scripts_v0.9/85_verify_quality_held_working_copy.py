import hashlib
import json
from collections import Counter
from pathlib import Path

BASE = Path("data/interim")
SOURCE = BASE / "instruction_leakage_clean_v0.9"
OUTPUT = BASE / "instruction_quality_held_working_v0.9"
MANIFEST = BASE / "instruction_quality_hold_manifest_v0.9.json"
QUEUE = BASE / "instruction_quality_decision_queue_14_v0.9.csv"
AUDIT = OUTPUT / "quality_hold_audit.json"

SPLITS = ("train", "validation", "test")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
audit = json.loads(AUDIT.read_text(encoding="utf-8"))

queue_sha256 = hashlib.sha256(QUEUE.read_bytes()).hexdigest()

if queue_sha256 != manifest["source_review_sha256"]:
    raise ValueError("Karar listesi SHA-256 özeti uyuşmuyor.")

if audit["source_queue_sha256"] != queue_sha256:
    raise ValueError("Çalışma kopyası denetim özeti uyuşmuyor.")

if manifest["training_approved"] is not False:
    raise ValueError("Manifestoda beklenmeyen eğitim onayı.")

if audit["training_approved"] is not False:
    raise ValueError("Çalışma kopyasında beklenmeyen eğitim onayı.")

if audit["rights_status"] != "pending_review":
    raise ValueError("Kaynak hakları durumu beklenenden farklı.")

hold_records = manifest["hold_records"]
hold_ids = {row["record_id"] for row in hold_records}

if len(hold_records) != 14 or len(hold_ids) != 14:
    raise ValueError("Manifestoda 14 benzersiz kayıt bekleniyordu.")

counts = Counter()
held = Counter()
retained = Counter()
seen_held = set()

print("LEXITECH TR - CALISMA KOPYASI BUTUNLUK KONTROLU")
print("=" * 65)

for split in SPLITS:
    source_path = SOURCE / f"{split}.jsonl"
    output_path = OUTPUT / f"{split}.jsonl"

    with (
        source_path.open("rb") as original,
        output_path.open("rb") as working
    ):
        for source_line in original:
            if not source_line.strip():
                continue

            record = json.loads(source_line)
            record_id = record["id"]
            counts[split] += 1

            if record_id in hold_ids:
                if record_id in seen_held:
                    raise ValueError("Bekletilen kayıt tekrarlı.")

                expected_split = next(
                    row["split"]
                    for row in hold_records
                    if row["record_id"] == record_id
                )

                if expected_split != split:
                    raise ValueError(
                        "Bekletilen kaydın split bilgisi hatalı."
                    )

                seen_held.add(record_id)
                held[split] += 1
                continue

            output_line = working.readline()

            if not output_line:
                raise ValueError(
                    f"{split}: Çalışma kopyasında eksik kayıt var."
                )

            if source_line != output_line:
                raise ValueError(
                    f"{split}: İçerik veya sıra değişmiş! "
                    f"Kaynak ID: {record_id}"
                )

            output_record = json.loads(output_line)

            if output_record["id"] != record_id:
                raise ValueError(
                    f"{split}: Kayıt kimliği uyuşmuyor."
                )

            retained[split] += 1

        if working.readline():
            raise ValueError(
                f"{split}: Çalışma kopyasında fazladan kayıt var."
            )

    if counts[split] != manifest["original_split_counts"][split]:
        raise ValueError(f"{split}: Kaynak kayıt sayısı uyuşmuyor.")

    if held[split] != manifest["held_split_counts"][split]:
        raise ValueError(f"{split}: Bekletilen kayıt sayısı uyuşmuyor.")

    if retained[split] != manifest[
        "proposed_remaining_split_counts"
    ][split]:
        raise ValueError(f"{split}: Kalan kayıt sayısı uyuşmuyor.")

    if retained[split] != audit["output_counts"][split]:
        raise ValueError(f"{split}: Denetim raporu uyuşmuyor.")

    print(f"\n{split.upper()}")
    print("Orijinal:", counts[split])
    print("Bekletilen:", held[split])
    print("Birebir aynı korunan:", retained[split])
    print("Bütünlük kontrolü: BAŞARILI")

if seen_held != hold_ids:
    raise ValueError("Bekletilen 14 kaydın tamamı bulunamadı.")

if sum(counts.values()) != 124510:
    raise ValueError("Kaynak toplamı hatalı.")

if sum(held.values()) != 14:
    raise ValueError("Bekletme toplamı hatalı.")

if sum(retained.values()) != 124496:
    raise ValueError("Çalışma kopyası toplamı hatalı.")

if audit["total_output"] != 124496:
    raise ValueError("Denetim raporundaki toplam hatalı.")

print("\n" + "=" * 65)
print("TOPLAM ORIJINAL QA:", sum(counts.values()))
print("TOPLAM BEKLETILEN:", sum(held.values()))
print("BIREBIR KORUNAN QA:", sum(retained.values()))
print("ICERIK VE SIRA KONTROLU: BASARILI")
print("MANIFESTO VE DENETIM UYUMU: BASARILI")
print("EGITIM ONAYI: HAYIR")
print("KAYNAK HAKLARI: INCELEME BEKLIYOR")
print("DOSYALAR DEGISTIRILMEDI")

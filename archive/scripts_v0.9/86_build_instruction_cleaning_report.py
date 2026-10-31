import json
import csv
import hashlib
from collections import Counter
from pathlib import Path

STATS = Path("reports/quality")
BASE = Path("data/interim")

SCAN = STATS / "instruction_quality_signals_v0.9.json"
QUEUE = BASE / "instruction_quality_decision_queue_14_v0.9.csv"
MANIFEST = BASE / "instruction_quality_hold_manifest_v0.9.json"
AUDIT = BASE / "instruction_quality_held_working_v0.9/quality_hold_audit.json"
HEADLINES = BASE / "instruction_headline_review_13_v0.9.csv"

JSON_OUT = STATS / "instruction_cleaning_and_exclusion_v0.9.json"
MD_OUT = STATS / "instruction_cleaning_and_exclusion_v0.9.md"

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit("Rapor zaten mevcut; üzerine yazılmadı.")

scan = json.loads(SCAN.read_text(encoding="utf-8"))
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
audit = json.loads(AUDIT.read_text(encoding="utf-8"))

def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

queue = load_csv(QUEUE)
headlines = load_csv(HEADLINES)

if scan["total_qa"] != 124510:
    raise ValueError("Tarama toplamı uyuşmuyor.")

if scan["total_candidates"] != 2678:
    raise ValueError("Tarama adayı sayısı uyuşmuyor.")

if scan["schema_errors"] != 0:
    raise ValueError("Yapısal okuma hatası bulundu.")

if len(queue) != 14 or len(headlines) != 13:
    raise ValueError("İnceleme listelerinin boyutları uyuşmuyor.")

ids = [row["record_id"] for row in queue]

if len(set(ids)) != 14:
    raise ValueError("Tekrarlı kayıt kimliği bulundu.")

if any(
    row["recommended_treatment"]
    != "hold_from_future_training_pending_review"
    or row["final_human_decision"].strip()
    for row in queue
):
    raise ValueError("Bekletme veya insan kararı durumu değişmiş.")

sha = hashlib.sha256(QUEUE.read_bytes()).hexdigest()

if sha != manifest["source_review_sha256"]:
    raise ValueError("Manifesto ile karar listesi uyuşmuyor.")

if sha != audit["source_queue_sha256"]:
    raise ValueError("Denetim ile karar listesi uyuşmuyor.")

if (
    manifest["training_approved"] is not False
    or audit["training_approved"] is not False
    or audit["rights_status"] != "pending_review"
):
    raise ValueError("Eğitim onayı veya hak durumu beklenenden farklı.")

if (
    audit["total_original"] != 124510
    or audit["total_held"] != 14
    or audit["total_output"] != 124496
):
    raise ValueError("Çalışma kopyası toplamları uyuşmuyor.")

split_names = ("train", "validation", "test")

for split in split_names:
    if (
        audit["original_counts"][split]
        != manifest["original_split_counts"][split]
        or audit["held_counts"][split]
        != manifest["held_split_counts"][split]
        or audit["output_counts"][split]
        != manifest["proposed_remaining_split_counts"][split]
    ):
        raise ValueError(f"{split}: rapor sayıları uyuşmuyor.")

if scan["signal_counts"].get(
    "short_question_without_question_mark"
) != 268:
    raise ValueError("Kısa soru tarama sayısı uyuşmuyor.")

if Counter(x["prompt_form"] for x in headlines) != {
    "headline": 11,
    "statement": 2,
}:
    raise ValueError("Başlık/önerme dağılımı uyuşmuyor.")

reason_counts = Counter(
    reason
    for row in queue
    for reason in row["quality_reasons"].split("|")
)

expected_reasons = {
    "citation_only_answer": 1,
    "headline_prompt": 11,
    "incomplete_question_fragment": 1,
    "statement_prompt": 2,
}

if dict(reason_counts) != expected_reasons:
    raise ValueError("Bekletme gerekçeleri uyuşmuyor.")

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "advisor_questions": [5, 6],
    "scope": "instruction_quality_scan_and_preliminary_hold",
    "total_scanned_qa": 124510,
    "structural_errors": 0,
    "heuristic_candidate_qa": 2678,
    "heuristic_candidate_percentage": 2.151,
    "quality_signal_counts": scan["signal_counts"],
    "candidate_split_counts": scan["candidate_splits"],
    "short_prompt_analysis": {
        "initial_candidates": 268,
        "first_rule_explicit": 218,
        "improved_rule_explicit": 253,
        "additional_assistant_assessed_instructions": 2,
        "headline_or_statement_review": 13,
        "headline": 11,
        "statement": 2,
        "independent_human_validation": False,
    },
    "preliminary_hold": {
        "unique_records": 14,
        "reason_counts": dict(reason_counts),
        "source_queue_sha256": sha,
        "held_split_counts": manifest["held_split_counts"],
        "human_final_decisions": 0,
    },
    "working_copy": {
        "location": "data/interim/instruction_quality_held_working_v0.9",
        "original_counts": audit["original_counts"],
        "excluded_from_copy": audit["held_counts"],
        "remaining_counts": audit["output_counts"],
        "total_remaining": 124496,
        "original_dataset_unchanged": True,
        "byte_level_integrity_check": "passed_in_step_351",
    },
    "training_approved": False,
    "rights_status": "pending_review",
    "limitations": [
        "2678 aday kesin hatalı kayıt sayısı değildir.",
        "URL içeren metinler otomatik olarak hatalı değildir.",
        "14 kayıt geçici asistan önerisiyle çalışma kopyasında bekletildi.",
        "14 kaydın nihai insan kararı bulunmuyor.",
        "Bu rapor önceki bütün pipeline temizleme adımlarını kapsamaz.",
        "Diğer kalite adaylarının incelemesi tamamlanmadı.",
        "Kaynak hakları ve hukuki doğruluk ayrıca doğrulanmalı.",
        "Çalışma kopyası eğitim için onaylı değildir.",
    ],
}

lines = [
    "# LexiTech TR — Instruction Temizleme ve Eleme Raporu v0.9",
    "",
    "**Danışman soruları:** 5 (Temizleme), 6 (Eleme gerekçeleri)",
    "",
    "## Kapsam",
    "",
    "Bu rapor, Instruction Dataset üzerinde yapılan son "
    "kalite sinyali taramasını, asistanın ön değerlendirmelerini "
    "ve geçici bekletme filtresini belgeler. "
    "Bütün geçmiş veri temizleme işlemlerinin tam dökümü değildir.",
    "",
    "## Otomatik kalite taraması",
    "",
    "- Taranan QA: **124.510**",
    "- İnceleme adayı: **2.678 (%2,151)**",
    "- Yapısal okuma hatası: **0**",
    "",
    "| İşaretleme kuralı | Sayı |",
    "|---|---:|",
]

for key, count in sorted(
    scan["signal_counts"].items(),
    key=lambda x: (-x[1], x[0])
):
    lines.append(f"| `{key}` | {count:,} |")

lines += [
    "",
    "**Not:** Bir kayıt birden fazla belirti taşıyabilir. "
    "URL veya soru işareti eksikliği tek başına hata kanıtı değildir.",
    "",
    "## Kısa talimat kontrolü",
    "",
    "- Başlangıçta işaretlenen kısa metin: **268**",
    "- İlk kuralla açık talimat eşleşmesi: **218**",
    "- İyileştirilmiş kuralla eşleşme: **253**",
    "- İlave asistan ön incelemesiyle açık talimat: **2**",
    "- Başlık veya önerme incelemesine alınan: **13**",
    "  - Başlık: **11**",
    "  - Önerme: **2**",
    "",
    "## Geçici bekletme kararı",
    "",
    "- Benzersiz QA: **14**",
    "- Nihai insan kararı: **0**",
    "",
    "| Gerekçe | İşaret sayısı |",
    "|---|---:|",
]

for key, count in sorted(reason_counts.items()):
    lines.append(f"| `{key}` | {count} |")

lines += [
    "",
    "Gerekçe sayılarının toplamı 14'ten büyük olabilir; "
    "aynı kayıt birden fazla gerekçe taşıyabilir.",
    "",
    "## Çalışma kopyası ve bütünlük",
    "",
    "| Split | Orijinal | Bekletilen | Kopyada kalan |",
    "|---|---:|---:|---:|",
]

for split in split_names:
    lines.append(
        f"| {split} | {audit['original_counts'][split]:,} | "
        f"{audit['held_counts'][split]} | "
        f"{audit['output_counts'][split]:,} |"
    )

lines += [
    "| **Toplam** | **124.510** | **14** | **124.496** |",
    "",
    "Adım 351'de kalan kayıtların bayt düzeyinde içeriği "
    "ve sırası orijinal kayıtlarla karşılaştırılarak "
    "doğrulandı. Orijinal veri seti değiştirilmedi.",
    "",
    "## Eğitim ve lisans durumu",
    "",
    "- `training_approved = false`",
    "- `rights_status = pending_review`",
    "- Geçici filtre, eğitim izni veya hukuki doğruluk onayı değildir.",
    "",
    "## Sınırlılıklar",
    "",
]

for item in report["limitations"]:
    lines.append("- " + item)

lines += [
    "",
    "## Kanıt dosyaları",
    "",
    f"- Otomatik tarama: `{SCAN}`",
    f"- Birleştirilmiş karar listesi: `{QUEUE}`",
    f"- Bekletme manifestosu: `{MANIFEST}`",
    f"- Çalışma kopyası denetimi: `{AUDIT}`",
    "",
]

STATS.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

MD_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print("LEXITECH TR - TEMIZLEME VE ELEME RAPORU")
print("=" * 60)
print("Taranan QA:", report["total_scanned_qa"])
print("Kalite inceleme adayi:", report["heuristic_candidate_qa"])
print("Gecici bekletilen:", report["preliminary_hold"]["unique_records"])
print("Calisma kopyasinda kalan:", audit["total_output"])
print("Butunluk kontrolu: ADIM 351'DE BASARILI")
print("Nihai insan karari: 0")
print("Egitim onayi: HAYIR")
print("Kaynak haklari: INCELEME BEKLIYOR")
print("\nJSON:", JSON_OUT)
print("Markdown:", MD_OUT)
print("Ana veri setleri degistirilmedi.")

import csv
import hashlib
import json
from pathlib import Path

QUALITY = Path("reports/quality")
SPLITS = Path("reports/splits")
INTERIM = Path("data/interim")

PATHS = {
    "pool": QUALITY / "instruction_citation_pool_v0.9.json",
    "plan": SPLITS / "instruction_split_plan_v0.9.json",
    "dedup": QUALITY / "instruction_dedup_report_v0.9.json",
    "leakage": QUALITY / "instruction_leakage_fix_v0.9.json",
    "signals": QUALITY / "instruction_quality_signals_v0.9.json",
    "queue": INTERIM / "instruction_quality_decision_queue_14_v0.9.csv",
    "manifest": INTERIM / "instruction_quality_hold_manifest_v0.9.json",
    "audit": (
        INTERIM
        / "instruction_quality_held_working_v0.9"
        / "quality_hold_audit.json"
    ),
}

JSON_OUT = QUALITY / "instruction_full_cleaning_accounting_v0.9.json"
MD_OUT = QUALITY / "instruction_full_cleaning_accounting_v0.9.md"

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit(
        "Rapor dosyası zaten var. Üzerine yazılmadı."
    )

def read_json(key):
    return json.loads(
        PATHS[key].read_text(encoding="utf-8")
    )

pool = read_json("pool")
plan = read_json("plan")
dedup = read_json("dedup")
leakage = read_json("leakage")
signals = read_json("signals")
manifest = read_json("manifest")
audit = read_json("audit")

with PATHS["queue"].open(
    encoding="utf-8-sig",
    newline=""
) as f:
    queue = list(csv.DictReader(f))

start = pool["counts"]["total"]
candidates = pool["counts"]["review_candidates"]
not_selected = start - candidates

pc = plan["counts"]
reference_hold = pc["reference_review_quarantine"]
source_hold = pc["missing_source_quarantine"]
other_source_hold = pc.get(
    "other_missing_source_quarantine", 0
)
first_dataset = pc["provisional_candidates"]

dc = dedup["counts"]
alternative = dc["alternative_answer_records"]
identical = dc["identical_answer_duplicates_skipped"]
after_dedup = dc["kept"]

leakage_hold = sum(
    leakage["quarantined_counts"].values()
)
after_leakage = sum(
    leakage["new_counts"].values()
)

quality_hold = audit["total_held"]
working_copy = audit["total_output"]

queue_hash = hashlib.sha256(
    PATHS["queue"].read_bytes()
).hexdigest()

assert start == 308009
assert candidates == 131045
assert not_selected == 176964

assert reference_hold == 933
assert source_hold == 960
assert other_source_hold == 0

assert (
    candidates
    == reference_hold
    + source_hold
    + other_source_hold
    + first_dataset
)

assert first_dataset == 129152

assert (
    first_dataset
    == alternative + identical + after_dedup
)
assert alternative == 4630
assert identical == 7
assert after_dedup == 124515

assert leakage_hold == 5
assert after_dedup == leakage_hold + after_leakage
assert after_leakage == 124510

assert quality_hold == 14
assert after_leakage == quality_hold + working_copy
assert working_copy == 124496

assert len(queue) == 14
assert len({x["record_id"] for x in queue}) == 14
assert signals["total_candidates"] == 2678

assert manifest["source_review_sha256"] == queue_hash
assert audit["source_queue_sha256"] == queue_hash
assert manifest["training_approved"] is False
assert audit["training_approved"] is False
assert audit["rights_status"] == "pending_review"

assert all(
    x["recommended_treatment"]
    == "hold_from_future_training_pending_review"
    and not x["final_human_decision"].strip()
    for x in queue
)

stages = [
    {
        "stage": "Instruction aday secimi",
        "input": start,
        "set_aside": not_selected,
        "remaining": candidates,
        "decision_type": "heuristic_scope_selection",
        "evidence": "pool",
        "note": (
            "Secim kriterlerini karsilamayanlar hatali "
            "veya silinmis olarak yorumlanamaz."
        ),
    },
    {
        "stage": "Atif inceleme karantinasi",
        "input": candidates,
        "set_aside": reference_hold,
        "remaining": candidates - reference_hold,
        "decision_type": "pending_reference_review",
        "evidence": "plan",
        "note": "Atif uyumsuzlugu kesin hukuki hata kaniti degildir.",
    },
    {
        "stage": "Kaynak belgesi karantinasi",
        "input": candidates - reference_hold,
        "set_aside": source_hold + other_source_hold,
        "remaining": first_dataset,
        "decision_type": "pending_source_review",
        "evidence": "plan",
        "note": "Karantina, kalici silme karari degildir.",
    },
    {
        "stage": "Alternatif cevaplarin ayrilmasi",
        "input": first_dataset,
        "set_aside": alternative,
        "remaining": first_dataset - alternative,
        "decision_type": "alternative_answer_separation",
        "evidence": "dedup",
        "note": (
            "Alternatif cevap kayitlari ayrildi; "
            "bunlarin yanlis oldugu kanitlanmadi."
        ),
    },
    {
        "stage": "Ayni cevapli tekrarlar",
        "input": first_dataset - alternative,
        "set_aside": identical,
        "remaining": after_dedup,
        "decision_type": "duplicate_skip",
        "evidence": "dedup",
        "note": "Ayni cevapli 7 tekrar atlandi.",
    },
    {
        "stage": "Splitler arasi leakage duzeltmesi",
        "input": after_dedup,
        "set_aside": leakage_hold,
        "remaining": after_leakage,
        "decision_type": "cross_split_quarantine",
        "evidence": "leakage",
        "note": (
            "Validation'dan 4 ve testten 1 kayit ayrildi; "
            "raporlanan capraz-split soru gruplari sifira indi."
        ),
    },
    {
        "stage": "Gecici kalite bekletme",
        "input": after_leakage,
        "set_aside": quality_hold,
        "remaining": working_copy,
        "decision_type": "assistant_preliminary_hold",
        "evidence": "audit",
        "note": (
            "Yalnizca calisma kopyasindan ayrildi. "
            "Nihai insan karari yok."
        ),
    },
]

for i, stage in enumerate(stages):
    assert (
        stage["input"] - stage["set_aside"]
        == stage["remaining"]
    )
    if i > 0:
        assert stages[i - 1]["remaining"] == stage["input"]

split_rows = []

for split in ("train", "validation", "test"):
    original = audit["original_counts"][split]
    held = audit["held_counts"][split]
    remaining = audit["output_counts"][split]

    assert original - held == remaining

    split_rows.append({
        "split": split,
        "original": original,
        "held": held,
        "working_copy": remaining,
    })

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "advisor_questions": [5, 6],
    "scope": (
        "Instruction Dataset: exact_unique sonrasi "
        "aday seciminden kalite bekletmeli calisma "
        "kopyasina kadar kayit muhasebesi"
    ),
    "stages": stages,
    "quality_scan": {
        "scanned": 124510,
        "heuristic_review_candidates": 2678,
        "preliminary_held": 14,
        "final_human_decisions": 0,
    },
    "working_copy_splits": split_rows,
    "source_queue_sha256": queue_hash,
    "evidence_files": {
        key: str(path)
        for key, path in PATHS.items()
    },
    "previous_integrity_test": (
        "Adim 351: 124496 korunan kaydin "
        "bayt duzeyinde karsilastirmasi PASS"
    ),
    "limitations": [
        "Bu muhasebe 308009 kayitlik exact_unique asamasindan baslar.",
        "Ham veri indirme ve ilk exact dedup asamalari kapsam disidir.",
        "Kanun metinleri/domain corpus temizligi ayri bir is akisidir.",
        "176964 kayda tek bir hata gerekcesi atfedilemez.",
        "4630 alternatif cevap kaydi hatali ilan edilmemistir.",
        "2678 heuristik aday kesin hatali kayit sayisi degildir.",
        "14 gecici bekletme icin nihai insan karari yoktur.",
        "Bagimsiz hukuki dogruluk ve kaynak incelemesi tamamlanmadi.",
        "Kullanim haklari ve egitim izni henuz onaylanmadi.",
    ],
    "training_approved": False,
    "rights_status": "pending_review",
}

lines = [
    "# LexiTech TR — Instruction Veri Temizleme ve Eleme Muhasebesi v0.9",
    "",
    "**Danışman soruları:** 5 — Temizleme; 6 — Eleme gerekçeleri.",
    "",
    "## Kapsam",
    "",
    "Bu muhasebe `exact_unique` aşamasındaki 308.009 "
    "kayıttan başlayarak kalite bekletmeli çalışma "
    "kopyasındaki 124.496 kayda kadar olan işlemleri açıklar.",
    "",
    "Ham veriden ilk exact dedup aşamasına geçiş ve "
    "Domain Corpus temizliği bu raporun kapsamı dışındadır.",
    "",
    "## Kronolojik kayıt muhasebesi",
    "",
    "| Aşama | Başlangıç | Ayrılan | Kalan |",
    "|---|---:|---:|---:|",
]

for stage in stages:
    lines.append(
        f"| {stage['stage']} | "
        f"{stage['input']:,} | "
        f"{stage['set_aside']:,} | "
        f"{stage['remaining']:,} |"
    )

lines += [
    "",
    "## Ayrılan kayıtların anlamı",
    "",
]

for stage in stages:
    lines += [
        f"### {stage['stage']}",
        "",
        f"- **İşlem türü:** `{stage['decision_type']}`",
        f"- **Açıklama:** {stage['note']}",
        f"- **Kanıt:** `{PATHS[stage['evidence']]}`",
        "",
    ]

lines += [
    "## Son kalite taraması",
    "",
    "- Otomatik taranan: **124.510 QA**",
    "- Heuristik inceleme adayı: **2.678 QA**",
    "- Geçici bekletilen: **14 QA**",
    "- Nihai insan kararı: **0**",
    "",
    "## Çalışma kopyasının split dağılımı",
    "",
    "| Split | Orijinal | Bekletilen | Çalışma kopyası |",
    "|---|---:|---:|---:|",
]

for row in split_rows:
    lines.append(
        f"| {row['split']} | {row['original']:,} | "
        f"{row['held']} | {row['working_copy']:,} |"
    )

lines += [
    "| **Toplam** | **124.510** | **14** | **124.496** |",
    "",
    "Adım 351'de 124.496 korunan kaydın içeriği "
    "ve sırası bayt düzeyinde karşılaştırılarak "
    "doğrulandı. Kaynak dosyalar değiştirilmedi.",
    "",
    "## Sınırlılıklar",
    "",
]

for limitation in report["limitations"]:
    lines.append("- " + limitation)

lines += [
    "",
    "## Onay durumu",
    "",
    "- `training_approved = false`",
    "- `rights_status = pending_review`",
    "- Bu rapor veri kullanım veya eğitim izni sağlamaz.",
    "",
    "## Kanıt dosyaları",
    "",
]

for key, path in PATHS.items():
    lines.append(f"- `{key}`: `{path}`")

lines.append("")

QUALITY.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

MD_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print("LEXITECH TR - TAM INSTRUCTION ELEME MUHASEBESI")
print("=" * 65)
print("Baslangic QA:", start)
print("Aday secimi disinda kalan:", not_selected)
print("Atif karantinasi:", reference_hold)
print("Kaynak karantinasi:", source_hold + other_source_hold)
print("Alternatif cevaplar:", alternative)
print("Ayni cevapli tekrarlar:", identical)
print("Leakage karantinasi:", leakage_hold)
print("Gecici kalite bekletmesi:", quality_hold)
print("Son calisma kopyasi:", working_copy)
print("Kronolojik muhasebe: PASS")
print("Kaynak manifesto kontrolu: PASS")
print("Egitim onayi: HAYIR")
print("Kaynak haklari: INCELEME BEKLIYOR")
print("\nJSON:", JSON_OUT)
print("Markdown:", MD_OUT)
print("Ana veri setleri degistirilmedi.")

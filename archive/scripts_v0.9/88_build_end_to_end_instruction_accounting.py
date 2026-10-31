import json
from pathlib import Path

BASE = Path("data")
QUALITY = Path("reports/quality")

PREVIOUS = QUALITY / "instruction_full_cleaning_accounting_v0.9.json"

JSON_OUT = QUALITY / "instruction_end_to_end_accounting_v0.9.json"
MD_OUT = QUALITY / "instruction_end_to_end_accounting_v0.9.md"

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit("Rapor mevcut; üzerine yazılmadı.")

previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))

sources = {
    "sinanelms/hukukisorular": "sinanelms__hukukisorular",
    "OrionCAF/turkish_law_qa_dataset": "OrionCAF__turkish_law_qa_dataset",
}

def count_jsonl(path):
    with path.open("rb") as f:
        return sum(1 for line in f if line.strip())

source_counts = {}
raw_total = 0
clean_total = 0

for name, folder in sources.items():
    raw = count_jsonl(BASE / "raw" / folder / "train.jsonl")
    clean = count_jsonl(
        BASE / "cleaned" / folder / "train.jsonl"
    )

    source_counts[name] = {
        "raw": raw,
        "cleaned": clean,
        "removed_by_initial_cleaning": raw - clean,
    }

    raw_total += raw
    clean_total += clean

unique_count = count_jsonl(
    BASE / "deduplicated" / "exact_unique.jsonl"
)

assert raw_total == 378903
assert clean_total == 378902
assert unique_count == 308009

assert source_counts["sinanelms/hukukisorular"] == {
    "raw": 360598,
    "cleaned": 360597,
    "removed_by_initial_cleaning": 1,
}

assert source_counts["OrionCAF/turkish_law_qa_dataset"] == {
    "raw": 18305,
    "cleaned": 18305,
    "removed_by_initial_cleaning": 0,
}

stages = [
    {
        "name": "İlk metin temizliği",
        "input": raw_total,
        "set_aside": raw_total - clean_total,
        "remaining": clean_total,
        "classification": "empty_question_or_answer_filter",
        "evidence": "scripts/03_clean.py",
    },
    {
        "name": "Birebir tekrar ayıklama",
        "input": clean_total,
        "set_aside": clean_total - unique_count,
        "remaining": unique_count,
        "classification": "exact_duplicate",
        "evidence": "scripts/05_exact_deduplicate.py",
    },
]

stages.extend(previous["stages"])

for i, stage in enumerate(stages):
    if stage["input"] - stage["set_aside"] != stage["remaining"]:
        raise ValueError(
            f"Muhasebe hatası: {stage.get('name', stage.get('stage'))}"
        )

    if i and stages[i - 1]["remaining"] != stage["input"]:
        raise ValueError(
            f"Aşamalar arasında kopukluk: {stage.get('name', stage.get('stage'))}"
        )

total_set_aside = sum(
    stage["set_aside"] for stage in stages
)

final_count = stages[-1]["remaining"]

assert len(stages) == 9
assert total_set_aside == 254407
assert final_count == 124496
assert raw_total - total_set_aside == final_count

assert previous["training_approved"] is False
assert previous["rights_status"] == "pending_review"

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "advisor_questions": [5, 6],
    "scope": "raw_qa_to_quality_held_instruction_working_copy",
    "source_counts": source_counts,
    "initial_raw_records": raw_total,
    "stages": stages,
    "total_not_carried_forward": total_set_aside,
    "final_working_copy_records": final_count,
    "all_arithmetic_checks_passed": True,
    "previous_report": str(PREVIOUS),
    "training_approved": False,
    "rights_status": "pending_review",
    "limitations": [
        "Ayrılan kayıtların tamamı hatalı veya silinmiş değildir.",
        "İlk temizlemede ayrılan tek kaydın bireysel "
        "gerekçesi ayrıca doğrulanmalıdır.",
        "İlk exact dedup kontrolü soru ve cevap içeriğine dayanır.",
        "Instruction seçim havuzu hukuken doğrulanmış değildir.",
        "Alternatif cevaplar ve karantina kayıtları "
        "kesin hatalı kabul edilmemiştir.",
        "2678 kalite sinyali adayı kesin hata sayısı değildir.",
        "14 kayıt yalnızca çalışma kopyasında bekletilmiştir.",
        "Domain Corpus temizleme geçmişi ayrı raporlanmalıdır.",
        "Kaynak kullanım hakları ve bağımsız hukuki "
        "doğrulama tamamlanmamıştır.",
        "Bu rapor eğitim için izin vermez.",
    ],
}

lines = [
    "# LexiTech TR — Uçtan Uca Instruction Veri Muhasebesi v0.9",
    "",
    "**Danışman soruları:** 5 ve 6",
    "",
    "## Kaynak bazında başlangıç",
    "",
    "| Kaynak | Ham | Temizlenmiş | İlk temizlemede ayrılan |",
    "|---|---:|---:|---:|",
]

for name, stats in source_counts.items():
    lines.append(
        f"| {name} | {stats['raw']:,} | "
        f"{stats['cleaned']:,} | "
        f"{stats['removed_by_initial_cleaning']:,} |"
    )

lines += [
    f"| **Toplam** | **{raw_total:,}** | "
    f"**{clean_total:,}** | **{raw_total - clean_total:,}** |",
    "",
    "## Kronolojik veri muhasebesi",
    "",
    "| Aşama | Girdi | Ayrılan | Kalan |",
    "|---|---:|---:|---:|",
]

for stage in stages:
    lines.append(
        f"| {stage.get('name', stage.get('stage'))} | {stage['input']:,} | "
        f"{stage['set_aside']:,} | {stage['remaining']:,} |"
    )

lines += [
    "",
    "## Muhasebe doğrulaması",
    "",
    f"- Ham veri: **{raw_total:,}** kayıt",
    f"- Son çalışma kopyasına aktarılmayan: "
    f"**{total_set_aside:,}** kayıt",
    f"- Son çalışma kopyası: **{final_count:,}** kayıt",
    "- Aşamalar arası sayısal tutarlılık: **PASS**",
    "",
    "## İlk temizleme yöntemleri",
    "",
    "- HTML entity çözme",
    "- HTML etiketlerini kaldırma",
    "- Unicode NFC normalizasyonu",
    "- Boşluk, tab ve satır sonu normalizasyonu",
    "- Boş soru veya cevap içeren kayıtları ayırma",
    "",
    "## Birebir tekrar ayıklama",
    "",
    "Temizlenmiş soru ve cevap birlikte SHA-256 ile "
    "karşılaştırıldı. Kaynak adı hash hesabına alınmadı.",
    "",
    "Adım 360'ta 308.009 kaydın saklanan içerik "
    "özetleri yeniden hesaplandı: hatalı veya tekrarlı "
    "özet bulunmadı.",
    "",
    "## Eleme ve karantina ayrımı",
    "",
    "Yukarıdaki 'ayrılan' sütunu kalıcı silme anlamına "
    "gelmez. Kayıtlar farklı aşamalarda seçim dışı "
    "bırakılmış, karantinaya alınmış veya alternatif "
    "cevap grubuna ayrılmış olabilir.",
    "",
    "## Sınırlılıklar",
    "",
]

for item in report["limitations"]:
    lines.append("- " + item)

lines += [
    "",
    "## Eğitim ve kullanım hakkı durumu",
    "",
    "- `training_approved = false`",
    "- `rights_status = pending_review`",
    "",
    f"**Önceki ayrıntılı rapor:** `{PREVIOUS}`",
    "",
]

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

MD_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print("LEXITECH TR - UCTAN UCA INSTRUCTION MUHASEBESI")
print("=" * 65)
print("Ham QA:", raw_total)
print("Ilk temizleme ayrilan:", raw_total - clean_total)
print("Exact dedup ayrilan:", clean_total - unique_count)
print("Exact unique QA:", unique_count)
print("Toplam ayri tutulan:", total_set_aside)
print("Son calisma kopyasi:", final_count)
print("Muhasebe kontrolu: PASS")
print("Egitim onayi: HAYIR")
print("Kaynak haklari: INCELEME BEKLIYOR")
print("\nJSON:", JSON_OUT)
print("Markdown:", MD_OUT)
print("Ana veri setleri degistirilmedi.")

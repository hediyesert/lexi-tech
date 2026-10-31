import csv
import json
from collections import Counter
from pathlib import Path

SOURCES = Path("reports/sources")
QUALITY = Path("reports/quality")

HF_FILE = SOURCES / "hf_license_evidence_v0.9.csv"
AUDIT_FILE = SOURCES / "source_rights_audit_v0.9.csv"
LAW_FILE = SOURCES / "legislation_documents.csv"

JSON_OUT = QUALITY / "source_rights_gap_report_v0.9.json"
MD_OUT = QUALITY / "source_rights_gap_report_v0.9.md"

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit(
        "Rapor zaten var. Mevcut dosyanin uzerine yazilmadi."
    )

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

hf = read_csv(HF_FILE)
audit = read_csv(AUDIT_FILE)
laws = read_csv(LAW_FILE)

assert len(hf) == 2
assert len(audit) == 22
assert len(laws) == 12

def is_false(value):
    return str(value).strip().lower() == "false"

assert all(
    is_false(row["training_approved"])
    and is_false(row["redistribution_approved"])
    and row["review_status"].strip() == "pending"
    for row in audit
)

assert all(
    row["training_permission_status"] == "pending_review"
    and row["redistribution_permission_status"] == "pending_review"
    and row["underlying_content_rights"] == "unverified"
    for row in hf
)

assert all(
    row["rights_status"] == "incelenecek"
    for row in laws
)

source_types = Counter(
    row["source_type"] for row in audit
)

license_statuses = Counter(
    row["published_license"] for row in audit
)

missing_document_urls = sum(
    not row.get("document_url", "").strip()
    for row in laws
)

hf_details = []

for row in hf:
    hf_details.append({
        "dataset": row["dataset"],
        "dataset_url": row["dataset_url"],
        "evidence_url": row["evidence_url"],
        "observed_date": row["observed_date"],
        "published_license": row["published_license"],
        "reported_origin": row["reported_origin"],
        "underlying_content_rights":
            row["underlying_content_rights"],
        "training_permission_status":
            row["training_permission_status"],
        "redistribution_permission_status":
            row["redistribution_permission_status"],
        "required_action": row["required_action"],
        "notes": row["notes"],
    })

actions = [
    {
        "priority": 1,
        "subject": "sinanelms/hukukisorular",
        "action": (
            "Veri seti lisansini ve kaynak makalelerin "
            "egitim/turev kullanim izinlerini kanitla."
        ),
    },
    {
        "priority": 1,
        "subject": "OrionCAF/turkish_law_qa_dataset",
        "action": (
            "Yayinci Apache-2.0 beyaninin kapsamini "
            "ve ozgun kaynaklarin haklarini dogrula."
        ),
    },
    {
        "priority": 1,
        "subject": "12 resmi kanun belgesi",
        "action": (
            "Belgeye ozel kaynak URL'lerini, metin "
            "surumlerini, kullanim ve dagitim "
            "kosullarini incele."
        ),
    },
    {
        "priority": 2,
        "subject": "8 ek kaynak kaydi",
        "action": (
            "Kaynak izlerini tekil QA kayitlariyla "
            "eslestir; izin ve lisans kanitlarini topla."
        ),
    },
    {
        "priority": 2,
        "subject": "Kisisel veri ve hukuki dogruluk",
        "action": (
            "Kisisel veri taramasi ve bagimsiz "
            "hukuki kalite incelemesini tamamla."
        ),
    },
    {
        "priority": 2,
        "subject": "Surum ve dokumantasyon",
        "action": (
            "124510 ana veri surumu ile 124496 "
            "gecici calisma kopyasini ayri belgele."
        ),
    },
]

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "scope": "source_rights_evidence_gaps",
    "audit_entry_count": len(audit),
    "audit_source_type_counts": dict(source_types),
    "audit_license_status_counts": dict(license_statuses),
    "training_approved_entries": 0,
    "redistribution_approved_entries": 0,
    "pending_review_entries": len(audit),
    "huggingface_datasets": hf_details,
    "legislation_document_count": len(laws),
    "legislation_missing_document_urls": missing_document_urls,
    "actions": actions,
    "evidence_files": [
        str(HF_FILE),
        str(AUDIT_FILE),
        str(LAW_FILE),
        "DATASET_CARD.md",
        "INSTRUCTION_CARD.md",
    ],
    "notes": [
        "Bu bir mevcut kanit envanteri raporudur.",
        "Lisans beyanlari bagimsiz olarak "
        "yeniden dogrulanmamistir.",
        "22 denetim kaydi, 22 ayri veri seti "
        "anlamina gelmez.",
        "Resmi kanun metinleri ile ucuncu taraf "
        "veri setleri ayri degerlendirilmelidir.",
        "Onay verilmemis olmasi otomatik olarak "
        "kesin hukuki yasak anlamina gelmez.",
        "Teknik kalite PASS sonuclari kullanim "
        "izni veya hukuki dogruluk kaniti degildir.",
    ],
    "training_approved": False,
    "rights_status": "pending_review",
}

lines = [
    "# LexiTech TR — Kaynak Hakları ve İzin Eksikleri v0.9",
    "",
    "## İncelemenin kapsamı",
    "",
    "Mevcut kaynak envanterini ve veri seti "
    "yayıncılarının daha önce kaydedilmiş "
    "lisans beyanlarını inceledim. Bu çalışma "
    "bağımsız bir hukuki lisans görüşü değildir.",
    "",
    f"- Kaynak hakları denetim kaydı: **{len(audit)}**",
    f"- Hugging Face veri seti: **{len(hf)}**",
    f"- Kanun belgesi: **{len(laws)}**",
    f"- Eğitim onayı verilen denetim kaydı: **0**",
    f"- Dağıtım onayı verilen denetim kaydı: **0**",
    f"- İncelemesi bekleyen kayıt: **{len(audit)}**",
    "",
    "## Kaynak türleri",
    "",
]

for source_type, count in sorted(source_types.items()):
    lines.append(f"- `{source_type}`: {count}")

lines += [
    "",
    "## Hugging Face lisans kanıtları",
    "",
    "| Veri seti | Yayıncı lisans bilgisi | "
    "Özgün kaynak hakları | Eğitim izni |",
    "|---|---|---|---|",
]

for item in hf_details:
    lines.append(
        f"| `{item['dataset']}` | "
        f"`{item['published_license']}` | "
        f"`{item['underlying_content_rights']}` | "
        f"`{item['training_permission_status']}` |"
    )

lines += [
    "",
    "Her iki veri seti için yayıncı beyanları "
    "kaydedildi; fakat özgün kaynakların kullanım "
    "hakları doğrulanmadı. Özellikle bir veri setinde "
    "yazılı lisans bilgisinin bulunması, üçüncü "
    "taraf içeriklerin aynı kapsamda lisanslandığını "
    "tek başına kanıtlamaz.",
    "",
    "## Resmî mevzuat kaynakları",
    "",
    "12 kanun belgesinin PDF ve temiz metin SHA-256 "
    "bütünlüğü doğrulandı. Buna rağmen belge "
    "sürümleri ve kullanım koşulları için "
    "ayrı inceleme gereklidir.",
    "",
    f"- Envanterde belgeye özel URL'si boş olan: "
    f"**{missing_document_urls}/12**",
    "",
    "## Öncelikli eksikler",
    "",
]

for item in actions:
    lines.append(
        f"- **Öncelik {item['priority']} — "
        f"{item['subject']}:** {item['action']}"
    )

lines += [
    "",
    "## Sınırlılıklar",
    "",
]

for note in report["notes"]:
    lines.append("- " + note)

lines += [
    "",
    "## Sonuç",
    "",
    "Mevcut aşamada veri kaynakları için model "
    "eğitimine veya yeniden dağıtıma onay vermedim. "
    "Kaynak haklarını, kişisel veri durumunu ve "
    "hukuki doğruluğu doğrulamadan veri setini "
    "eğitime hazır olarak sunmuyorum.",
    "",
    "- `training_approved = false`",
    "- `rights_status = pending_review`",
    "",
    "## Kanıt dosyaları",
    "",
]

for path in report["evidence_files"]:
    lines.append(f"- `{path}`")

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

print("LEXITECH TR - KAYNAK HAKLARI EKSIK KANIT RAPORU")
print("=" * 65)
print("Denetim kaydi:", len(audit))
print("Kaynak turleri:", dict(source_types))
print("Hugging Face veri seti:", len(hf))
print("Kanun belgesi:", len(laws))
print("Belgeye ozel URL eksigi:", missing_document_urls)
print("Egitim onayli kayit: 0")
print("Dagitim onayli kayit: 0")
print("Inceleme bekleyen kayit:", len(audit))
print("Kaynak haklari kontrolu: PASS")
print("Egitim onayi: HAYIR")
print("\nJSON:", JSON_OUT)
print("Markdown:", MD_OUT)
print("Ana veri setleri degistirilmedi.")

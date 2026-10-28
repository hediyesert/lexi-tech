import csv
import json
import shutil
from collections import Counter
from pathlib import Path

SOURCE_FILE = Path(
    "reports/sources/legislation_documents.csv"
)

OUTPUT = Path(
    "reports/sources/source_rights_audit_v0.9.csv"
)

SUMMARY = Path(
    "reports/quality/source_rights_summary_v0.9.json"
)

REPORT_DATE = "2026-10-27"

records = []

# 1. Resmî mevzuat kaynakları
with SOURCE_FILE.open(
    encoding="utf-8-sig", newline=""
) as f:
    documents = list(csv.DictReader(f))

if len(documents) != 12:
    raise ValueError(
        f"12 kanun kaynağı bekleniyordu: {len(documents)}"
    )

for doc in documents:
    law = str(
        doc.get("law_number")
        or doc.get("kanun_no")
        or ""
    ).strip()

    records.append({
        "source_id": f"legislation_{law}",
        "source_type": "official_legislation",
        "source_name": (
            doc.get("title")
            or doc.get("law_title")
            or doc.get("document_title")
            or f"Kanun {law}"
        ),
        "source_url": (
            doc.get("document_url")
            or doc.get("source_url")
            or ""
        ),
        "published_license": "not_assessed",
        "published_license_evidence": "",
        "underlying_rights": "review_required",
        "provenance_status": "local_pdf_metadata_available",
        "redistribution_approved": "false",
        "training_approved": "false",
        "review_status": "pending",
        "review_notes": (
            "Resmi mevzuat PDF kaynagi. "
            "Metin surumu, atif, kullanim haklari ve "
            "yeniden dagitim kosullari incelenmeli."
        ),
        "audit_date": REPORT_DATE,
    })

# 2. Hugging Face veri setleri
records.extend([
    {
        "source_id": "hf_sinanelms_hukukisorular",
        "source_type": "third_party_qa_dataset",
        "source_name": "sinanelms/hukukisorular",
        "source_url": (
            "https://huggingface.co/datasets/"
            "sinanelms/hukukisorular"
        ),
        "published_license": "unclear",
        "published_license_evidence": (
            "Sayfada MIT ifadesi ornek egitim kodunun "
            "icinde gorunuyor; veri seti lisansi olarak "
            "dogrulanamadi."
        ),
        "underlying_rights": "review_required",
        "provenance_status": (
            "publisher_reports_scraped_articles_"
            "and_gemini_generated_qa"
        ),
        "redistribution_approved": "false",
        "training_approved": "false",
        "review_status": "pending",
        "review_notes": (
            "Yayinci, hukuk sitelerindeki makalelerden "
            "Gemini ile soru-cevap urettigini belirtiyor. "
            "Kaynak makale haklari ve turev kullanim "
            "izinleri dogrulanmadi."
        ),
        "audit_date": REPORT_DATE,
    },
    {
        "source_id": "hf_orioncaf_turkish_law_qa",
        "source_type": "third_party_qa_dataset",
        "source_name": "OrionCAF/turkish_law_qa_dataset",
        "source_url": (
            "https://huggingface.co/datasets/"
            "OrionCAF/turkish_law_qa_dataset"
        ),
        "published_license": "apache-2.0_publisher_claim",
        "published_license_evidence": (
            "Hugging Face dataset card license alaninda "
            "apache-2.0 belirtiliyor."
        ),
        "underlying_rights": "review_required",
        "provenance_status": (
            "publisher_describes_legislation_"
            "case_law_and_articles"
        ),
        "redistribution_approved": "false",
        "training_approved": "false",
        "review_status": "pending",
        "review_notes": (
            "Apache-2.0 yayinci beyani kaydedildi. "
            "Ozgun kaynak haklari, veri kokenselliği "
            "ve hukuki dogruluk ayrica incelenmeli."
        ),
        "audit_date": REPORT_DATE,
    },
])

# 3. Sinanelms açıklamasında belirtilen üçüncü taraf siteler.
# Bunların gerçekten her kayıt için kullanıldığını
# doğrulamıyoruz; kaynak beyanı olarak kaydediyoruz.
third_party_domains = [
    "ayboga.com.tr",
    "barandogan.av.tr",
    "kadimhukuk.com.tr",
    "kalemci.av.tr",
    "oner.av.tr",
    "or.av.tr",
    "sen.av.tr",
    "zulkufarslan.com.tr",
]

for domain in third_party_domains:
    records.append({
        "source_id": "upstream_" + domain,
        "source_type": "reported_upstream_website",
        "source_name": domain,
        "source_url": "https://" + domain,
        "published_license": "not_verified",
        "published_license_evidence": "",
        "underlying_rights": "review_required",
        "provenance_status": "reported_by_dataset_publisher",
        "redistribution_approved": "false",
        "training_approved": "false",
        "review_status": "pending",
        "review_notes": (
            "sinanelms veri seti aciklamasinda "
            "kaynak site olarak geciyor. "
            "Sayfanin lisansi, kullanim izni ve "
            "tekil QA ile baglantisi dogrulanmadi."
        ),
        "audit_date": REPORT_DATE,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
SUMMARY.parent.mkdir(parents=True, exist_ok=True)

if OUTPUT.exists():
    backup = OUTPUT.with_suffix(".csv.backup")
    shutil.copy2(OUTPUT, backup)
    print("Eski rapor yedeklendi:", backup)

fields = list(records[0])

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)

types = Counter(
    record["source_type"] for record in records
)

summary = {
    "version": "v0.9",
    "audit_date": REPORT_DATE,
    "total_source_entries": len(records),
    "source_types": dict(types),
    "source_rights_approved_count": 0,
    "training_approved_count": 0,
    "evidence_urls": [
        "https://huggingface.co/datasets/"
        "sinanelms/hukukisorular",
        "https://huggingface.co/datasets/"
        "OrionCAF/turkish_law_qa_dataset",
    ],
    "important_notes": [
        "Yayinci lisans beyani altta yatan tum "
        "kaynak haklarini otomatik kanitlamaz.",
        "sinanelms icin veri seti lisansi net degil.",
        "Resmi mevzuat metinleri icin guncellik ve "
        "dagitim kosullari ayrica incelenmeli.",
        "Kaynak sitelerin tek tek izinleri "
        "bu adimda kontrol edilmedi.",
        "Hicbir veri setine egitim onayi verilmedi."
    ]
}

SUMMARY.write_text(
    json.dumps(
        summary, ensure_ascii=False, indent=2
    ),
    encoding="utf-8"
)

print("LEXITECH TR - KAYNAK HAKLARI DENETİMİ")
print("=" * 60)
print("Toplam kaynak girdisi:", len(records))

for source_type, count in sorted(types.items()):
    print(f"  {source_type}: {count}")

print("Eğitim için onaylı kaynak:", 0)
print("Yeniden dağıtım için onaylı kaynak:", 0)
print("Kaynak tablosu:", OUTPUT)
print("Özet rapor:", SUMMARY)
print("Mevcut veri setleri değiştirilmedi.")

import csv
from pathlib import Path

OUTPUT = Path(
    "reports/sources/hf_license_evidence_v0.9.csv"
)

rows = [
    {
        "dataset": "sinanelms/hukukisorular",
        "dataset_url": "https://huggingface.co/datasets/sinanelms/hukukisorular",
        "evidence_url": "https://huggingface.co/datasets/sinanelms/hukukisorular/blob/main/README.md",
        "observed_date": "2026-10-28",
        "published_license": "not_explicitly_declared_in_card_metadata",
        "reported_origin": "third_party_legal_articles_and_gemini_2.5_pro_generation",
        "underlying_content_rights": "unverified",
        "training_permission_status": "pending_review",
        "redistribution_permission_status": "pending_review",
        "required_action": "verify_dataset_license_and_upstream_article_permissions",
        "notes": "MIT text inside example training code is not sufficient evidence of a dataset license"
    },
    {
        "dataset": "OrionCAF/turkish_law_qa_dataset",
        "dataset_url": "https://huggingface.co/datasets/OrionCAF/turkish_law_qa_dataset",
        "evidence_url": "https://huggingface.co/datasets/OrionCAF/turkish_law_qa_dataset/blob/main/README.md",
        "observed_date": "2026-10-28",
        "published_license": "apache-2.0_publisher_declared",
        "reported_origin": "turkish_legislation_case_law_and_legal_articles",
        "underlying_content_rights": "unverified",
        "training_permission_status": "pending_review",
        "redistribution_permission_status": "pending_review",
        "required_action": "verify_upstream_provenance_and_license_scope",
        "notes": "Publisher license declaration does not independently verify third-party source rights"
    }
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

if OUTPUT.exists():
    raise SystemExit(
        "Kanıt dosyası zaten mevcut. "
        "Üzerine yazılmadı: " + str(OUTPUT)
    )

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(rows[0])
    )
    writer.writeheader()
    writer.writerows(rows)

print("LEXITECH TR - HF LİSANS KANITLARI")
print("=" * 55)

for row in rows:
    print("\nKaynak:", row["dataset"])
    print("Yayımlanan lisans:", row["published_license"])
    print("Özgün içerik hakları:", row["underlying_content_rights"])
    print("Eğitim izni:", row["training_permission_status"])
    print("Kanıt:", row["evidence_url"])

print("\nKaydedilen kaynak:", len(rows))
print("Kanıt dosyası:", OUTPUT)
print("Eğitim için yeni onay verilen kaynak: 0")
print("Mevcut veri setleri değiştirilmedi.")

import json
from pathlib import Path

QUALITY = Path("reports/quality")

SOURCE = QUALITY / "source_rights_gap_report_v0.9.json"
OUTPUT = QUALITY / "advisor_source_rights_v0.9.md"

if OUTPUT.exists():
    raise SystemExit(
        "Rapor zaten mevcut. Uzerine yazilmadi."
    )

data = json.loads(SOURCE.read_text(encoding="utf-8"))

assert data["audit_entry_count"] == 22
assert data["pending_review_entries"] == 22
assert data["training_approved_entries"] == 0
assert data["redistribution_approved_entries"] == 0
assert data["legislation_document_count"] == 12
assert data["legislation_missing_document_urls"] == 12
assert len(data["huggingface_datasets"]) == 2
assert data["training_approved"] is False
assert data["rights_status"] == "pending_review"

types = data["audit_source_type_counts"]

assert types["official_legislation"] == 12
assert types["third_party_qa_dataset"] == 2
assert types["reported_upstream_website"] == 8

lines = [
    "# LexiTech TR — Veri Kaynakları ve Kullanım Hakları",
    "",
    "**Rapor türü:** Danışmana sunulacak kaynak "
    "ve lisans değerlendirmesi",
    "",
    "**Sürüm:** v0.9",
    "",
    "## Veri kaynaklarını nasıl belirledim?",
    "",
    "LexiTech TR projemde veri kaynaklarını "
    "Instruction Dataset ve Domain Corpus "
    "olarak iki grupta ele aldım.",
    "",
    "Instruction Dataset için Hugging Face "
    "üzerinden iki Türkçe hukuk soru-cevap "
    "veri seti kullandım:",
    "",
    "- `sinanelms/hukukisorular`",
    "- `OrionCAF/turkish_law_qa_dataset`",
    "",
    "Domain Corpus için resmî mevzuat "
    "kaynaklarından elde edilen 12 kanun PDF'sini "
    "kullandım. Ham PDF dosyalarını, temiz "
    "metin sürümlerini ve SHA-256 özetlerini "
    "ayrı dosyalarda korudum.",
    "",
    "## Kaynak haklarını nasıl denetledim?",
    "",
    "Kaynak hakları için ayrı bir denetim "
    "envanteri hazırladım. Bu envanterde "
    "**22 kaynak kaydı** bulunuyor:",
    "",
    "- 12 resmî mevzuat kaydı",
    "- 2 üçüncü taraf QA veri seti kaydı",
    "- 8 bildirilen üst kaynak web sitesi kaydı",
    "",
    "Bu 22 kayıt, 22 bağımsız eğitim veri "
    "seti anlamına gelmemektedir.",
    "",
    "Her kaynak için yayımlanmış lisans "
    "bilgisini, kaynak kökenini, kullanım "
    "haklarını ve izin durumunu ayrı ayrı "
    "değerlendirmeye aldım.",
    "",
    "## Hugging Face veri setlerinde bulduklarım",
    "",
]

for item in data["huggingface_datasets"]:
    lines.extend([
        f"### {item['dataset']}",
        "",
        f"- Kaydedilen lisans durumu: "
        f"`{item['published_license']}`",
        f"- Bildirilen köken: `{item['reported_origin']}`",
        f"- Özgün içerik hakları: "
        f"`{item['underlying_content_rights']}`",
        f"- Eğitim izni: "
        f"`{item['training_permission_status']}`",
        f"- Yeniden dağıtım izni: "
        f"`{item['redistribution_permission_status']}`",
        f"- Gereken inceleme: "
        f"`{item['required_action']}`",
        "",
    ])

lines += [
    "Bu bilgiler, daha önce kaydettiğim "
    "yayıncı açıklamalarına ve lisans "
    "kanıtlarına dayanmaktadır. Bağımsız "
    "hukuki izin doğrulamasının tamamlandığı "
    "anlamına gelmemektedir.",
    "",
    "Özellikle yayıncının bir lisans beyan "
    "etmesi, veri setindeki üçüncü taraf "
    "metinlerin ve türev soru-cevapların "
    "haklarını otomatik olarak doğrulamaz.",
    "",
    "## Resmî kanun metinlerinin durumu",
    "",
    "12 kanunun ham PDF ve temiz metin "
    "dosyalarının SHA-256 bütünlüğünü "
    "doğruladım. Ancak dosya bütünlüğünün "
    "hukuki içerik doğruluğundan ve "
    "kullanım hakkından ayrı olduğunu "
    "gözetiyorum.",
    "",
    "Envanterde 12 kanunun tamamı için "
    "belgeye özel URL alanı boş. Bu "
    "nedenle kullanılan PDF sürümlerinin "
    "doğrudan kaynak bağlantılarının, "
    "güncelliğinin ve kullanım koşullarının "
    "ayrıca belgelenmesi gerekiyor.",
    "",
    "## Mevcut izin durumu",
    "",
    "İncelediğim 22 denetim kaydının tamamı "
    "beklemede. Hiçbir kayıt için proje "
    "kapsamında eğitim veya yeniden "
    "dağıtım onayı verilmiş değil.",
    "",
    "Bu durum, kaynakların kesin olarak "
    "yasaklandığı anlamına gelmez; "
    "yalnızca gerekli hukuki ve teknik "
    "incelemelerin tamamlanmadığını gösterir.",
    "",
    "## Tamamlamam gereken çalışmalar",
    "",
    "1. İki QA veri setinin özgün kaynaklarını "
    "ve lisans kapsamını doğrulamak.",
    "2. Üçüncü taraf web kaynaklarını "
    "ilgili kayıtlarla eşleştirmek.",
    "3. Kanun PDF'lerinin belgeye özel "
    "resmî URL'lerini ve sürüm tarihlerini "
    "envantere eklemek.",
    "4. Eğitim ve yeniden dağıtım "
    "koşullarını ayrıca değerlendirmek.",
    "5. Kişisel veri ve bağımsız hukuki "
    "kalite incelemelerini tamamlamak.",
    "",
    "## Sonuç",
    "",
    "Veri mühendisliği ve dosya bütünlüğü "
    "kontrollerini gerçekleştirdim. "
    "Bununla birlikte kaynak kullanım "
    "hakları doğrulanmadığı için veri "
    "setlerini model eğitimine veya "
    "yeniden dağıtıma onaylı olarak "
    "sunmuyorum.",
    "",
    "- `training_approved = false`",
    "- `rights_status = pending_review`",
    "",
    "## Kanıt dosyaları",
    "",
    "- `reports/sources/hf_license_evidence_v0.9.csv`",
    "- `reports/sources/source_rights_audit_v0.9.csv`",
    "- `reports/sources/legislation_documents.csv`",
    "- `reports/quality/source_rights_gap_report_v0.9.json`",
    "- `reports/quality/source_rights_gap_report_v0.9.md`",
    "- `DATASET_CARD.md`",
    "- `INSTRUCTION_CARD.md`",
    "",
]

OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("LEXITECH TR - DANISMAN KAYNAK HAKLARI RAPORU")
print("=" * 60)
print("Kaynak denetim kaydi:", 22)
print("Resmi mevzuat:", 12)
print("QA veri seti:", 2)
print("Ek web kaynagi:", 8)
print("Inceleme bekleyen:", 22)
print("Belgeye ozel URL eksigi:", 12)
print("Birinci tekil sahis raporu: OLUSTURULDU")
print("Rapor:", OUTPUT)
print("Egitim onayi: HAYIR")
print("Hak incelemesi: BEKLIYOR")
print("Ana veri setleri degistirilmedi.")

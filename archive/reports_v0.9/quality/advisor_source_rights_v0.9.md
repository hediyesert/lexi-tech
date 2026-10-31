# LexiTech TR — Veri Kaynakları ve Kullanım Hakları

**Rapor türü:** Danışmana sunulacak kaynak ve lisans değerlendirmesi

**Sürüm:** v0.9

## Veri kaynaklarını nasıl belirledim?

LexiTech TR projemde veri kaynaklarını Instruction Dataset ve Domain Corpus olarak iki grupta ele aldım.

Instruction Dataset için Hugging Face üzerinden iki Türkçe hukuk soru-cevap veri seti kullandım:

- `sinanelms/hukukisorular`
- `OrionCAF/turkish_law_qa_dataset`

Domain Corpus için resmî mevzuat kaynaklarından elde edilen 12 kanun PDF'sini kullandım. Ham PDF dosyalarını, temiz metin sürümlerini ve SHA-256 özetlerini ayrı dosyalarda korudum.

## Kaynak haklarını nasıl denetledim?

Kaynak hakları için ayrı bir denetim envanteri hazırladım. Bu envanterde **22 kaynak kaydı** bulunuyor:

- 12 resmî mevzuat kaydı
- 2 üçüncü taraf QA veri seti kaydı
- 8 bildirilen üst kaynak web sitesi kaydı

Bu 22 kayıt, 22 bağımsız eğitim veri seti anlamına gelmemektedir.

Her kaynak için yayımlanmış lisans bilgisini, kaynak kökenini, kullanım haklarını ve izin durumunu ayrı ayrı değerlendirmeye aldım.

## Hugging Face veri setlerinde bulduklarım

### sinanelms/hukukisorular

- Kaydedilen lisans durumu: `not_explicitly_declared_in_card_metadata`
- Bildirilen köken: `third_party_legal_articles_and_gemini_2.5_pro_generation`
- Özgün içerik hakları: `unverified`
- Eğitim izni: `pending_review`
- Yeniden dağıtım izni: `pending_review`
- Gereken inceleme: `verify_dataset_license_and_upstream_article_permissions`

### OrionCAF/turkish_law_qa_dataset

- Kaydedilen lisans durumu: `apache-2.0_publisher_declared`
- Bildirilen köken: `turkish_legislation_case_law_and_legal_articles`
- Özgün içerik hakları: `unverified`
- Eğitim izni: `pending_review`
- Yeniden dağıtım izni: `pending_review`
- Gereken inceleme: `verify_upstream_provenance_and_license_scope`

Bu bilgiler, daha önce kaydettiğim yayıncı açıklamalarına ve lisans kanıtlarına dayanmaktadır. Bağımsız hukuki izin doğrulamasının tamamlandığı anlamına gelmemektedir.

Özellikle yayıncının bir lisans beyan etmesi, veri setindeki üçüncü taraf metinlerin ve türev soru-cevapların haklarını otomatik olarak doğrulamaz.

## Resmî kanun metinlerinin durumu

12 kanunun ham PDF ve temiz metin dosyalarının SHA-256 bütünlüğünü doğruladım. Ancak dosya bütünlüğünün hukuki içerik doğruluğundan ve kullanım hakkından ayrı olduğunu gözetiyorum.

Envanterde 12 kanunun tamamı için belgeye özel URL alanı boş. Bu nedenle kullanılan PDF sürümlerinin doğrudan kaynak bağlantılarının, güncelliğinin ve kullanım koşullarının ayrıca belgelenmesi gerekiyor.

## Mevcut izin durumu

İncelediğim 22 denetim kaydının tamamı beklemede. Hiçbir kayıt için proje kapsamında eğitim veya yeniden dağıtım onayı verilmiş değil.

Bu durum, kaynakların kesin olarak yasaklandığı anlamına gelmez; yalnızca gerekli hukuki ve teknik incelemelerin tamamlanmadığını gösterir.

## Tamamlamam gereken çalışmalar

1. İki QA veri setinin özgün kaynaklarını ve lisans kapsamını doğrulamak.
2. Üçüncü taraf web kaynaklarını ilgili kayıtlarla eşleştirmek.
3. Kanun PDF'lerinin belgeye özel resmî URL'lerini ve sürüm tarihlerini envantere eklemek.
4. Eğitim ve yeniden dağıtım koşullarını ayrıca değerlendirmek.
5. Kişisel veri ve bağımsız hukuki kalite incelemelerini tamamlamak.

## Sonuç

Veri mühendisliği ve dosya bütünlüğü kontrollerini gerçekleştirdim. Bununla birlikte kaynak kullanım hakları doğrulanmadığı için veri setlerini model eğitimine veya yeniden dağıtıma onaylı olarak sunmuyorum.

- `training_approved = false`
- `rights_status = pending_review`

## Kanıt dosyaları

- `reports/sources/hf_license_evidence_v0.9.csv`
- `reports/sources/source_rights_audit_v0.9.csv`
- `reports/sources/legislation_documents.csv`
- `reports/quality/source_rights_gap_report_v0.9.json`
- `reports/quality/source_rights_gap_report_v0.9.md`
- `DATASET_CARD.md`
- `INSTRUCTION_CARD.md`

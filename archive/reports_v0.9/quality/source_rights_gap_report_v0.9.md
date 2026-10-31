# LexiTech TR — Kaynak Hakları ve İzin Eksikleri v0.9

## İncelemenin kapsamı

Mevcut kaynak envanterini ve veri seti yayıncılarının daha önce kaydedilmiş lisans beyanlarını inceledim. Bu çalışma bağımsız bir hukuki lisans görüşü değildir.

- Kaynak hakları denetim kaydı: **22**
- Hugging Face veri seti: **2**
- Kanun belgesi: **12**
- Eğitim onayı verilen denetim kaydı: **0**
- Dağıtım onayı verilen denetim kaydı: **0**
- İncelemesi bekleyen kayıt: **22**

## Kaynak türleri

- `official_legislation`: 12
- `reported_upstream_website`: 8
- `third_party_qa_dataset`: 2

## Hugging Face lisans kanıtları

| Veri seti | Yayıncı lisans bilgisi | Özgün kaynak hakları | Eğitim izni |
|---|---|---|---|
| `sinanelms/hukukisorular` | `not_explicitly_declared_in_card_metadata` | `unverified` | `pending_review` |
| `OrionCAF/turkish_law_qa_dataset` | `apache-2.0_publisher_declared` | `unverified` | `pending_review` |

Her iki veri seti için yayıncı beyanları kaydedildi; fakat özgün kaynakların kullanım hakları doğrulanmadı. Özellikle bir veri setinde yazılı lisans bilgisinin bulunması, üçüncü taraf içeriklerin aynı kapsamda lisanslandığını tek başına kanıtlamaz.

## Resmî mevzuat kaynakları

12 kanun belgesinin PDF ve temiz metin SHA-256 bütünlüğü doğrulandı. Buna rağmen belge sürümleri ve kullanım koşulları için ayrı inceleme gereklidir.

- Envanterde belgeye özel URL'si boş olan: **12/12**

## Öncelikli eksikler

- **Öncelik 1 — sinanelms/hukukisorular:** Veri seti lisansini ve kaynak makalelerin egitim/turev kullanim izinlerini kanitla.
- **Öncelik 1 — OrionCAF/turkish_law_qa_dataset:** Yayinci Apache-2.0 beyaninin kapsamini ve ozgun kaynaklarin haklarini dogrula.
- **Öncelik 1 — 12 resmi kanun belgesi:** Belgeye ozel kaynak URL'lerini, metin surumlerini, kullanim ve dagitim kosullarini incele.
- **Öncelik 2 — 8 ek kaynak kaydi:** Kaynak izlerini tekil QA kayitlariyla eslestir; izin ve lisans kanitlarini topla.
- **Öncelik 2 — Kisisel veri ve hukuki dogruluk:** Kisisel veri taramasi ve bagimsiz hukuki kalite incelemesini tamamla.
- **Öncelik 2 — Surum ve dokumantasyon:** 124510 ana veri surumu ile 124496 gecici calisma kopyasini ayri belgele.

## Sınırlılıklar

- Bu bir mevcut kanit envanteri raporudur.
- Lisans beyanlari bagimsiz olarak yeniden dogrulanmamistir.
- 22 denetim kaydi, 22 ayri veri seti anlamina gelmez.
- Resmi kanun metinleri ile ucuncu taraf veri setleri ayri degerlendirilmelidir.
- Onay verilmemis olmasi otomatik olarak kesin hukuki yasak anlamina gelmez.
- Teknik kalite PASS sonuclari kullanim izni veya hukuki dogruluk kaniti degildir.

## Sonuç

Mevcut aşamada veri kaynakları için model eğitimine veya yeniden dağıtıma onay vermedim. Kaynak haklarını, kişisel veri durumunu ve hukuki doğruluğu doğrulamadan veri setini eğitime hazır olarak sunmuyorum.

- `training_approved = false`
- `rights_status = pending_review`

## Kanıt dosyaları

- `reports/sources/hf_license_evidence_v0.9.csv`
- `reports/sources/source_rights_audit_v0.9.csv`
- `reports/sources/legislation_documents.csv`
- `DATASET_CARD.md`
- `INSTRUCTION_CARD.md`

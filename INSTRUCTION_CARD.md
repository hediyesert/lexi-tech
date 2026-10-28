# LexiTech TR — INSTRUCTION_CARD

**Sürüm:** Instruction Dataset v0.9 (ön taslak)
**Belge tarihi:** 2026-10-27
**Dil:** Türkçe
**Alan:** Türkiye hukuku
**Durum:** Eğitim için onaylanmadı.

## 1. Amaç

Türkçe hukuk soru-cevap biçimindeki instruction verilerini,
ileriki SFT çalışmaları için incelemek ve hazırlamak.

**Vize aşamasında model eğitimi gerçekleştirilmemiştir.**

## 2. Kaynaklar

İlk havuzda iki Hugging Face kaynağı değerlendirilmiştir:

- `sinanelms/hukukisorular`
- `OrionCAF/turkish_law_qa_dataset`

Başlangıç havuzu: **378.903 kayıt**.
Birebir tekrar giderilmiş ilk havuz: **308.009 kayıt**.
Madde göstergeli inceleme havuzu: **131.045 kayıt**.

Güncel ön taslaktaki kaynaklar:

- `sinanelms/hukukisorular`: 124,510 kayıt

Kaynaklara ait kullanım lisansları ve veri üretim
kökenleri **ayrıca doğrulanmalıdır**.

Kaynakta görülen `0.json`, `24.json` benzeri etiketler,
**resmî kanun belgesi kimliği değildir**.

## 3. Güncel veri kümesi

Toplam: **124,510** soru-cevap kaydı.

- Train: **111,782**
- Validation: **6,397**
- Test: **6,331**

Dosyalar:

- `data/interim/instruction_leakage_clean_v0.9/train.jsonl`
- `data/interim/instruction_leakage_clean_v0.9/validation.jsonl`
- `data/interim/instruction_leakage_clean_v0.9/test.jsonl`

Bunlar **ara aşama veri dosyalarıdır**; eğitim onayı
verilmiş nihai dosyalar değildir.

### Kanun bazında dağılım

| Kanun | Train | Validation | Test | Toplam |
|---|---:|---:|---:|---:|
| 2004 | 3,208 | 118 | 39 | 3,365 |
| 213 | 852 | 53 | 89 | 994 |
| 2577 | 4,509 | 288 | 152 | 4,949 |
| 2709 | 2,037 | 104 | 118 | 2,259 |
| 4721 | 11,714 | 387 | 183 | 12,284 |
| 4857 | 2,843 | 62 | 1 | 2,906 |
| 5237 | 47,206 | 2,959 | 4,221 | 54,386 |
| 5271 | 27,568 | 2,097 | 1,365 | 31,030 |
| 5510 | 1,580 | 18 | 8 | 1,606 |
| 6098 | 8,738 | 254 | 128 | 9,120 |
| 6102 | 1,201 | 54 | 24 | 1,279 |
| 6502 | 326 | 3 | 3 | 332 |

## 4. Veri şeması

Her kayıt şu alanları taşır:

- `id`
- `messages`: `user` sorusu ve `assistant` cevabı
- `metadata`: dil, kanun göstergesi, kaynak,
  kaynak dosya etiketi, split ve kalite bayrakları.

Kalite bayrakları arasında:

- `training_approved: false`
- `legal_accuracy_verified: false`
- `citation_accuracy_verified: false`
- `rights_status: pending_review`

Bu alanlar, otomatik işlemin hukuki doğrulama
yerine geçmediğini açıkça gösterir.

## 5. Seçim ve filtreleme

1. Kaynakların normalize edilmesi.
2. İlk birebir tekrarların kaldırılması.
3. Kanun ve madde göstergeleriyle aday havuzu oluşturulması.
4. Madde numarası yapısal kontrolü.
5. Şüpheli atıfların ve köken bilgisi yetersiz
   kayıtların geçici olarak ayrılması.
6. Kaynak dosya ve aynı soru bağlantılarına dayanan
   belge gruplu split planı.
7. Aynı sorunun alternatif cevap versiyonlarının
   inceleme havuzuna ayrılması.
8. Normalize edilmiş kümeler arası birebir soru
   sızıntısının giderilmesi.
9. Önceden belirlenmiş MinHash yakın tekrar çiftlerinin
   güncel veri setiyle karşılaştırılması.

## 6. Kayıt muhasebesi

Madde göstergeli havuz: **131.045**

- Şüpheli atıf nedeniyle ayrılan: **933**
- Kaynak kökeni yetersiz OrionCAF adayları: **960**
- İlk splitli ön taslak: **129.152**
- Alternatif cevaplı kayıtlar: **4.630**
- Eşdeğer tekrar nedeniyle atlanan kayıtlar: **7**
- Kümeler arası normalize soru tekrarı nedeniyle
  ayrılan kayıtlar: **5**
- Güncel ön taslak: **124,510**

Bu eleme gerekçeleri **hukuki doğruluk kararları
olarak yorumlanmamalıdır**.

## 7. Split ve sızıntı denetimi

- İlk plan: Kaynak dosya bağlantılı 74 grup.
- En büyük bağlantılı grup: 97.033 kayıt.
- Güncel splitlerde ortak kaynak dosya sayısı: **0**.
- Kontrol edilen normalize soru düzeyinde ortak
  train/validation/test soru sayısı: **0**.
- Eski MinHash raporundan güncel veri setinde
  kalan yakın tekrar çifti: **527**.
- Bunların farklı splitlerde bulunanı: **0**.
- Aynı split içindeki çiftler: **527**.

Önceki MinHash yöntemi soru **ve cevabı birlikte**
karşılaştırmış, üç kelimelik parçalar ve 0,85
Jaccard eşiği kullanmıştır.

**Sınırlama:** Güncel veri üzerinde yalnızca soru
metnine dayanan kapsamlı yeni yakın tekrar taraması
yapılmadı. Dolayısıyla sıfır sızıntı garantisi yoktur.

## 8. Dengesizlikler

Veriler özellikle Türk Ceza Kanunu ve Ceza
Muhakemesi Kanunu soruları bakımından yoğunlaşmaktadır.

İş Kanunu, sosyal sigorta, ticaret ve tüketici
hukuku alanlarında validation/test örneği
sayısı bazı kümelerde çok düşüktür.

Bu kümelerle her hukuk alanında aynı güvenilirlikte
performans ölçümü yapıldığı iddia edilmemelidir.

## 9. İnsan değerlendirmesi

200 soruluk tabakalı manuel değerlendirme örneklemi:

`reports/quality/instruction_manual_review_200_v0.9.csv`

Mevcut ilerleme:

- 1 kayıt: Ek inceleme gerekli.
- 1 kayıt: Geçici kabul.
- 198 kayıt: Henüz değerlendirilmedi.

**Nihai hukuk uzmanı onayı verilmedi.**

Örneklem kanun bazında tabakalıdır; genel veri
kümesinin rastgele ve temsili örneklemi değildir.

## 10. Hukuki ve etik riskler

- Yanlış kanun-madde eşleştirmeleri.
- Gerçekte doğrulanmamış yargı kararı atıfları.
- Tarihi geçmiş veya mevzuat değişikliklerinden
  etkilenmiş cevaplar.
- Farklı cevap versiyonlarında eksik bilgi ve
  olası hukuki çelişkiler.
- Otomatik hazırlanmış veya üretim kökeni
  belirsiz kaynak metinleri.
- Kaynak lisanslarının ve kullanım izinlerinin
  henüz netleşmemiş olması.
- Soru-cevaplar üzerinden gerçek kişilere ilişkin
  kişisel veri risklerinin ayrıca incelenmesi gereği.

**Madde numarasının ilgili kanunda bulunması,
cevabın hukuken doğru olduğunu göstermez.**

## 11. İlgili denetim raporları

- `reports/quality/instruction_article_audit_v0.9.json`
- `reports/quality/instruction_reference_mismatches_v0.9.csv`
- `reports/splits/instruction_split_plan_v0.9.json`
- `reports/quality/instruction_split_integrity_v0.9.json`
- `reports/quality/instruction_dedup_report_v0.9.json`
- `reports/quality/instruction_balance_audit_v0.9.json`
- `reports/quality/instruction_leakage_fix_v0.9.json`
- `reports/quality/instruction_existing_near_duplicates_v0.9.json`

## 12. Eğitim ve paylaşım kısıtları

Güncel ön taslaktaki **124,510** kayıtta
`training_approved: false` bulunmaktadır.

**124,510** kaydın kullanım hakkı durumu
`pending_review` olarak işaretlidir.

Kaynak kullanım izinleri, kişisel veri incelemesi
ve hukuki kalite denetimleri tamamlanmadan
bu veri seti `v1.0` veya eğitim için onaylı
olarak sunulmamalıdır.

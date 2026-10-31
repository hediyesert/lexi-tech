# LexiTech TR — Instruction Temizleme ve Eleme Raporu v0.9

**Danışman soruları:** 5 (Temizleme), 6 (Eleme gerekçeleri)

## Kapsam

Bu rapor, Instruction Dataset üzerinde yapılan son kalite sinyali taramasını, asistanın ön değerlendirmelerini ve geçici bekletme filtresini belgeler. Bütün geçmiş veri temizleme işlemlerinin tam dökümü değildir.

## Otomatik kalite taraması

- Taranan QA: **124.510**
- İnceleme adayı: **2.678 (%2,151)**
- Yapısal okuma hatası: **0**

| İşaretleme kuralı | Sayı |
|---|---:|
| `url_in_answer` | 2,298 |
| `short_question_without_question_mark` | 268 |
| `url_in_question` | 117 |
| `possible_reference_only_answer` | 1 |

**Not:** Bir kayıt birden fazla belirti taşıyabilir. URL veya soru işareti eksikliği tek başına hata kanıtı değildir.

## Kısa talimat kontrolü

- Başlangıçta işaretlenen kısa metin: **268**
- İlk kuralla açık talimat eşleşmesi: **218**
- İyileştirilmiş kuralla eşleşme: **253**
- İlave asistan ön incelemesiyle açık talimat: **2**
- Başlık veya önerme incelemesine alınan: **13**
  - Başlık: **11**
  - Önerme: **2**

## Geçici bekletme kararı

- Benzersiz QA: **14**
- Nihai insan kararı: **0**

| Gerekçe | İşaret sayısı |
|---|---:|
| `citation_only_answer` | 1 |
| `headline_prompt` | 11 |
| `incomplete_question_fragment` | 1 |
| `statement_prompt` | 2 |

Gerekçe sayılarının toplamı 14'ten büyük olabilir; aynı kayıt birden fazla gerekçe taşıyabilir.

## Çalışma kopyası ve bütünlük

| Split | Orijinal | Bekletilen | Kopyada kalan |
|---|---:|---:|---:|
| train | 111,782 | 14 | 111,768 |
| validation | 6,397 | 0 | 6,397 |
| test | 6,331 | 0 | 6,331 |
| **Toplam** | **124.510** | **14** | **124.496** |

Adım 351'de kalan kayıtların bayt düzeyinde içeriği ve sırası orijinal kayıtlarla karşılaştırılarak doğrulandı. Orijinal veri seti değiştirilmedi.

## Eğitim ve lisans durumu

- `training_approved = false`
- `rights_status = pending_review`
- Geçici filtre, eğitim izni veya hukuki doğruluk onayı değildir.

## Sınırlılıklar

- 2678 aday kesin hatalı kayıt sayısı değildir.
- URL içeren metinler otomatik olarak hatalı değildir.
- 14 kayıt geçici asistan önerisiyle çalışma kopyasında bekletildi.
- 14 kaydın nihai insan kararı bulunmuyor.
- Bu rapor önceki bütün pipeline temizleme adımlarını kapsamaz.
- Diğer kalite adaylarının incelemesi tamamlanmadı.
- Kaynak hakları ve hukuki doğruluk ayrıca doğrulanmalı.
- Çalışma kopyası eğitim için onaylı değildir.

## Kanıt dosyaları

- Otomatik tarama: `reports/quality/instruction_quality_signals_v0.9.json`
- Birleştirilmiş karar listesi: `data/interim/instruction_quality_decision_queue_14_v0.9.csv`
- Bekletme manifestosu: `data/interim/instruction_quality_hold_manifest_v0.9.json`
- Çalışma kopyası denetimi: `data/interim/instruction_quality_held_working_v0.9/quality_hold_audit.json`

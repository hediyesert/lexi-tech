# LexiTech TR — Instruction Veri Temizleme ve Eleme Muhasebesi v0.9

**Danışman soruları:** 5 — Temizleme; 6 — Eleme gerekçeleri.

## Kapsam

Bu muhasebe `exact_unique` aşamasındaki 308.009 kayıttan başlayarak kalite bekletmeli çalışma kopyasındaki 124.496 kayda kadar olan işlemleri açıklar.

Ham veriden ilk exact dedup aşamasına geçiş ve Domain Corpus temizliği bu raporun kapsamı dışındadır.

## Kronolojik kayıt muhasebesi

| Aşama | Başlangıç | Ayrılan | Kalan |
|---|---:|---:|---:|
| Instruction aday secimi | 308,009 | 176,964 | 131,045 |
| Atif inceleme karantinasi | 131,045 | 933 | 130,112 |
| Kaynak belgesi karantinasi | 130,112 | 960 | 129,152 |
| Alternatif cevaplarin ayrilmasi | 129,152 | 4,630 | 124,522 |
| Ayni cevapli tekrarlar | 124,522 | 7 | 124,515 |
| Splitler arasi leakage duzeltmesi | 124,515 | 5 | 124,510 |
| Gecici kalite bekletme | 124,510 | 14 | 124,496 |

## Ayrılan kayıtların anlamı

### Instruction aday secimi

- **İşlem türü:** `heuristic_scope_selection`
- **Açıklama:** Secim kriterlerini karsilamayanlar hatali veya silinmis olarak yorumlanamaz.
- **Kanıt:** `reports/quality/instruction_citation_pool_v0.9.json`

### Atif inceleme karantinasi

- **İşlem türü:** `pending_reference_review`
- **Açıklama:** Atif uyumsuzlugu kesin hukuki hata kaniti degildir.
- **Kanıt:** `reports/splits/instruction_split_plan_v0.9.json`

### Kaynak belgesi karantinasi

- **İşlem türü:** `pending_source_review`
- **Açıklama:** Karantina, kalici silme karari degildir.
- **Kanıt:** `reports/splits/instruction_split_plan_v0.9.json`

### Alternatif cevaplarin ayrilmasi

- **İşlem türü:** `alternative_answer_separation`
- **Açıklama:** Alternatif cevap kayitlari ayrildi; bunlarin yanlis oldugu kanitlanmadi.
- **Kanıt:** `reports/quality/instruction_dedup_report_v0.9.json`

### Ayni cevapli tekrarlar

- **İşlem türü:** `duplicate_skip`
- **Açıklama:** Ayni cevapli 7 tekrar atlandi.
- **Kanıt:** `reports/quality/instruction_dedup_report_v0.9.json`

### Splitler arasi leakage duzeltmesi

- **İşlem türü:** `cross_split_quarantine`
- **Açıklama:** Validation'dan 4 ve testten 1 kayit ayrildi; raporlanan capraz-split soru gruplari sifira indi.
- **Kanıt:** `reports/quality/instruction_leakage_fix_v0.9.json`

### Gecici kalite bekletme

- **İşlem türü:** `assistant_preliminary_hold`
- **Açıklama:** Yalnizca calisma kopyasindan ayrildi. Nihai insan karari yok.
- **Kanıt:** `data/interim/instruction_quality_held_working_v0.9/quality_hold_audit.json`

## Son kalite taraması

- Otomatik taranan: **124.510 QA**
- Heuristik inceleme adayı: **2.678 QA**
- Geçici bekletilen: **14 QA**
- Nihai insan kararı: **0**

## Çalışma kopyasının split dağılımı

| Split | Orijinal | Bekletilen | Çalışma kopyası |
|---|---:|---:|---:|
| train | 111,782 | 14 | 111,768 |
| validation | 6,397 | 0 | 6,397 |
| test | 6,331 | 0 | 6,331 |
| **Toplam** | **124.510** | **14** | **124.496** |

Adım 351'de 124.496 korunan kaydın içeriği ve sırası bayt düzeyinde karşılaştırılarak doğrulandı. Kaynak dosyalar değiştirilmedi.

## Sınırlılıklar

- Bu muhasebe 308009 kayitlik exact_unique asamasindan baslar.
- Ham veri indirme ve ilk exact dedup asamalari kapsam disidir.
- Kanun metinleri/domain corpus temizligi ayri bir is akisidir.
- 176964 kayda tek bir hata gerekcesi atfedilemez.
- 4630 alternatif cevap kaydi hatali ilan edilmemistir.
- 2678 heuristik aday kesin hatali kayit sayisi degildir.
- 14 gecici bekletme icin nihai insan karari yoktur.
- Bagimsiz hukuki dogruluk ve kaynak incelemesi tamamlanmadi.
- Kullanim haklari ve egitim izni henuz onaylanmadi.

## Onay durumu

- `training_approved = false`
- `rights_status = pending_review`
- Bu rapor veri kullanım veya eğitim izni sağlamaz.

## Kanıt dosyaları

- `pool`: `reports/quality/instruction_citation_pool_v0.9.json`
- `plan`: `reports/splits/instruction_split_plan_v0.9.json`
- `dedup`: `reports/quality/instruction_dedup_report_v0.9.json`
- `leakage`: `reports/quality/instruction_leakage_fix_v0.9.json`
- `signals`: `reports/quality/instruction_quality_signals_v0.9.json`
- `queue`: `data/interim/instruction_quality_decision_queue_14_v0.9.csv`
- `manifest`: `data/interim/instruction_quality_hold_manifest_v0.9.json`
- `audit`: `data/interim/instruction_quality_held_working_v0.9/quality_hold_audit.json`

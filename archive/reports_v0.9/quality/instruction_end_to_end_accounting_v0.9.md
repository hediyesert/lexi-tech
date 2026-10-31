# LexiTech TR — Uçtan Uca Instruction Veri Muhasebesi v0.9

**Danışman soruları:** 5 ve 6

## Kaynak bazında başlangıç

| Kaynak | Ham | Temizlenmiş | İlk temizlemede ayrılan |
|---|---:|---:|---:|
| sinanelms/hukukisorular | 360,598 | 360,597 | 1 |
| OrionCAF/turkish_law_qa_dataset | 18,305 | 18,305 | 0 |
| **Toplam** | **378,903** | **378,902** | **1** |

## Kronolojik veri muhasebesi

| Aşama | Girdi | Ayrılan | Kalan |
|---|---:|---:|---:|
| İlk metin temizliği | 378,903 | 1 | 378,902 |
| Birebir tekrar ayıklama | 378,902 | 70,893 | 308,009 |
| Instruction aday secimi | 308,009 | 176,964 | 131,045 |
| Atif inceleme karantinasi | 131,045 | 933 | 130,112 |
| Kaynak belgesi karantinasi | 130,112 | 960 | 129,152 |
| Alternatif cevaplarin ayrilmasi | 129,152 | 4,630 | 124,522 |
| Ayni cevapli tekrarlar | 124,522 | 7 | 124,515 |
| Splitler arasi leakage duzeltmesi | 124,515 | 5 | 124,510 |
| Gecici kalite bekletme | 124,510 | 14 | 124,496 |

## Muhasebe doğrulaması

- Ham veri: **378,903** kayıt
- Son çalışma kopyasına aktarılmayan: **254,407** kayıt
- Son çalışma kopyası: **124,496** kayıt
- Aşamalar arası sayısal tutarlılık: **PASS**

## İlk temizleme yöntemleri

- HTML entity çözme
- HTML etiketlerini kaldırma
- Unicode NFC normalizasyonu
- Boşluk, tab ve satır sonu normalizasyonu
- Boş soru veya cevap içeren kayıtları ayırma

## Birebir tekrar ayıklama

Temizlenmiş soru ve cevap birlikte SHA-256 ile karşılaştırıldı. Kaynak adı hash hesabına alınmadı.

Adım 360'ta 308.009 kaydın saklanan içerik özetleri yeniden hesaplandı: hatalı veya tekrarlı özet bulunmadı.

## Eleme ve karantina ayrımı

Yukarıdaki 'ayrılan' sütunu kalıcı silme anlamına gelmez. Kayıtlar farklı aşamalarda seçim dışı bırakılmış, karantinaya alınmış veya alternatif cevap grubuna ayrılmış olabilir.

## Sınırlılıklar

- Ayrılan kayıtların tamamı hatalı veya silinmiş değildir.
- İlk temizlemede ayrılan tek kaydın bireysel gerekçesi ayrıca doğrulanmalıdır.
- İlk exact dedup kontrolü soru ve cevap içeriğine dayanır.
- Instruction seçim havuzu hukuken doğrulanmış değildir.
- Alternatif cevaplar ve karantina kayıtları kesin hatalı kabul edilmemiştir.
- 2678 kalite sinyali adayı kesin hata sayısı değildir.
- 14 kayıt yalnızca çalışma kopyasında bekletilmiştir.
- Domain Corpus temizleme geçmişi ayrı raporlanmalıdır.
- Kaynak kullanım hakları ve bağımsız hukuki doğrulama tamamlanmamıştır.
- Bu rapor eğitim için izin vermez.

## Eğitim ve kullanım hakkı durumu

- `training_approved = false`
- `rights_status = pending_review`

**Önceki ayrıntılı rapor:** `reports/quality/instruction_full_cleaning_accounting_v0.9.json`

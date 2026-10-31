# LexiTech TR — Dil Kalitesi Raporu v0.9

## Kapsam

- Danışman sorusu: **10 — Dil dağılımı**
- Instruction Dataset: **124.510 QA**
- Domain Corpus: **12 kanundan 60 örnek metin parçası**
- Yöntem: langdetect 1.0.9 ve asistan ön değerlendirmesi

## Instruction Dataset sonuçları

| Ölçüm | Soru | Cevap |
|---|---:|---:|
| Otomatik Türkçe | 124,389 | 124,508 |
| Asistan tarafından Türkçe görülen ek metin | 121 | 1 |
| Birleşik Türkçe değerlendirmesi | 124,510 | 124,509 |
| Dil durumu sınıflandırılamayan | 0 | 1 |

Birleşik değerlendirme, otomatik tespit ile asistanın ön incelemesini birlikte gösterir; **bağımsız insan tarafından doğrulanmış oran değildir.**

## Domain Corpus

- Belge: **12**
- İncelenen metin parçası: **60**
- Otomatik Türkçe tespit edilen: **60**

## İşaretli kayıt incelemesi

- Asistanın ön değerlendirdiği metin: **123**
- Türkçe görünen metin: **122**
- Dil açısından sınıflandırılamayan: **1**
- Ayrı soru kalitesi uyarısı: **2**
- Bağımsız insan uzman onayı: **0**

### Soru kalitesi uyarıları

- İnceleme #36: `source_url_contamination`
- İnceleme #120: `incomplete_question_fragment`

## Sınırlılıklar

- Dil tespiti langdetect 1.0.9 ile yapıldı.
- Otomatik dil tespiti ve olasılıkları hatasız değildir.
- 123 işaretli metin asistan tarafından ön değerlendirildi.
- Bağımsız insan uzman onayı bulunmuyor.
- Karma dil içeriği her zaman yakalanamayabilir.
- Domain sonucu bütün metnin değil 60 parçanın analizidir.
- İki soru kalitesi uyarısı henüz çözülmedi.
- Dil kontrolü hukuki doğruluğu veya kullanım hakkını kanıtlamaz.

## Sonuç

Dil dağılımı için tam otomatik Instruction taraması ve işaretli metinlerin asistan ön incelemesi tamamlandı. Bağımsız doğrulama ve iki soru kalitesi sorununun çözümü sonraki aşamalar için açık kaldı.

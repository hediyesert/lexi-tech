# LexiTech TR — Dil Kalitesi Raporu v0.9.1

**Danışman sorusu:** 10 — Dil dağılımı

Bu sürüm v0.9 raporundaki kalite uyarısı alanlarını düzeltir.

## Instruction Dataset

| Ölçüm | Soru | Cevap |
|---|---:|---:|
| Otomatik Türkçe | 124,389 | 124,508 |
| Asistanın ek Türkçe ön değerlendirmesi | 121 | 1 |
| Birleşik Türkçe değerlendirmesi | 124,510 | 124,509 |
| Sınıflandırılamayan | 0 | 1 |

**Önemli:** Birleşik sonuç bağımsız insan tarafından doğrulanmış dil oranı değildir.

## Domain Corpus

- Kanun sayısı: 12
- İncelenen metin parçası: 60
- Otomatik Türkçe: 60/60

## Soru ve cevap kalitesi sorunları

- İnceleme 36: **Cevap** — `citation_only_answer`
- İnceleme 120: **Soru** — `incomplete_question_fragment`

Bu sorunlar dil hatasıyla aynı şey değildir.

## Sınırlılıklar

- Otomatik dil tespiti hatasız değildir.
- Asistan değerlendirmesi bağımsız uzman onayı değildir.
- Bir cevap dil açısından sınıflandırılamadı.
- Domain sonucu 60 örnek metin parçasına dayanır.
- Karma dil içeriği her zaman tespit edilemeyebilir.
- Soru ve cevap kalitesi sorunları henüz giderilmedi.
- Dil analizi hukuki doğruluğu ve lisansı kanıtlamaz.

## Sonuç

Tam Instruction otomatik taraması ve işaretlenen 123 metnin asistan ön incelemesi tamamlandı. Bağımsız doğrulama ve veri kalitesi düzeltmeleri henüz tamamlanmadı.

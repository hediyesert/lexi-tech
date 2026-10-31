# LexiTech TR — Görev Türü Kalite Raporu v0.9.2

## Kapsam

- Danışman sorusu: **15**
- Veri seti: **124.510 soru-cevap kaydı**
- Yöntem: kural ve anahtar kelime tabanlı sınıflandırma
- Durum: **Deneysel; nihai olarak onaylanmadı**

## Değerlendirme sonuçları

| Ölçüm | Sonuç |
|---|---:|
| Geliştirme örnekleri | 70 |
| Geliştirme uyumu | 30/70 |
| Ayrı tutulan test örnekleri | 50 |
| Test uyumu | 37/50 (%74,00) |
| Bağımsız insan uzman onayı | 0 |

## Tahmin kategorilerine göre test sonucu

| Tahmin kategorisi | Örnek | Uyumlu | Farklı |
|---|---:|---:|---:|
| article_explanation | 5 | 4 | 1 |
| case_application | 5 | 4 | 1 |
| case_law_analysis | 5 | 5 | 0 |
| comparison | 5 | 4 | 1 |
| definition | 5 | 1 | 4 |
| legal_conditions | 5 | 5 | 0 |
| legal_effect | 5 | 4 | 1 |
| other | 5 | 0 | 5 |
| penalty_sanction | 5 | 5 | 0 |
| procedure_deadline | 5 | 5 | 0 |

## Veri seti görev dağılımı

| Görev türü | Kayıt | Yüzde |
|---|---:|---:|
| other | 61125 | %49.09 |
| procedure_deadline | 14646 | %11.76 |
| definition | 13918 | %11.18 |
| legal_conditions | 11646 | %9.35 |
| case_law_analysis | 9470 | %7.61 |
| comparison | 6956 | %5.59 |
| case_application | 2742 | %2.20 |
| legal_effect | 2399 | %1.93 |
| penalty_sanction | 1597 | %1.28 |
| article_explanation | 11 | %0.01 |

## Sınırlılıklar ve sonraki işler

- **%74**, eşit kategorili 50 örnekte asistan etiketleriyle uyumdur; tüm veri setinin doğruluğu değildir.
- Test örnekleri geliştirme örneklerinden ayrı tutulmuştur ancak bağımsız insan tarafından etiketlenmemiştir.
- `other` oranı yüksek olduğundan sınıflandırıcı iyileştirme ve ek analiz gerektirir.
- Görev sınıflandırması, hukuki cevapların doğruluğunu veya kullanım izinlerini kanıtlamaz.
- Bağımsız insan incelemesi ve dağılıma uygun rastgele örneklem değerlendirmesi gereklidir.

## Sonuç

Danışmanın 15. sorusu için sayısal dağılım ve ön kalite analizi hazırlanmıştır. Bağımsız doğrulama tamamlanmadığı için nihai kabul verilmemiştir.

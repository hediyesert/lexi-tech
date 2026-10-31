# LexiTech TR — Danışman Soruları 10 ve 15

**Proje:** LexiTech TR

**Analiz edilen Instruction sürümü:** 124.510 QA; 14 kayıtlık kalite bekletmesi öncesi.

## 10. Veri setinin dil dağılımını nasıl belirledim?

Instruction Dataset'teki 124.510 soru-cevap kaydının soru ve cevap alanlarını ayrı ayrı otomatik dil tespitinden geçirdim. Otomatik sınıflandırmanın kesinleştiremediği işaretli metinler için asistan destekli ön değerlendirme yaptım.

| Dil değerlendirmesi | Soru | Cevap |
|---|---:|---:|
| Otomatik Türkçe | 124,389 | 124,508 |
| Asistanın Türkçe ön değerlendirmesi | 121 | 1 |
| Birleşik Türkçe sonucu | 124,510 | 124,509 |
| Sınıflandırılamayan | 0 | 1 |

Toplam 123 işaretli metin için asistan ön değerlendirmesi yapıldı. Bunların 122'si Türkçe olarak ön değerlendirildi; bir cevap dil açısından sınıflandırılamadı.

Domain Corpus tarafında ise 12 kanun belgesinden alınmış 60 metin parçasını inceledim. Otomatik dil tespiti 60 parçanın tamamını Türkçe olarak sınıflandırdı.

**Sınırlılık:** Bu sonuçlar bağımsız insan onayından geçmedi. Özellikle Domain Corpus değerlendirmesi bütün metinler yerine 60 örnek parçayı kapsamaktadır. Dil analizi hukuki doğruluğu göstermez.

## 15. Veri setinde hangi görev türleri var ve bunların kalitesini nasıl değerlendirdim?

124.510 soru-cevap kaydını kural ve anahtar kelime tabanlı deneysel bir görev sınıflandırıcısı ile kategorilere ayırdım. Sınıflandırıcıyı geliştirmek için 70 örnek kullandım; geliştirme aşamasından ayrı tutulan 50 örnek üzerinde ön değerlendirme yaptım.

### Görev türü dağılımı

| Görev türü | Kayıt | Oran |
|---|---:|---:|
| `other` | 61,125 | %49.09 |
| `procedure_deadline` | 14,646 | %11.76 |
| `definition` | 13,918 | %11.18 |
| `legal_conditions` | 11,646 | %9.35 |
| `case_law_analysis` | 9,470 | %7.61 |
| `comparison` | 6,956 | %5.59 |
| `case_application` | 2,742 | %2.20 |
| `legal_effect` | 2,399 | %1.93 |
| `penalty_sanction` | 1,597 | %1.28 |
| `article_explanation` | 11 | %0.01 |

### Ön kalite değerlendirmesi

- Geliştirme örnekleri: **70**
- Geliştirme uyumu: **30/70**
- Ayrı tutulan test örnekleri: **50**
- Test uyumu: **37/50 (%74.00)**
- Bağımsız insan uzman doğrulaması: **Yok**

Test örnekleri tahmin edilen görev kategorilerine göre dengeli seçildi. Etiketler bağımsız uzmanlardan değil, asistanın önerdiği ön etiketlerden geldi. Dolayısıyla %74 uyumu, gerçek sınıflandırma doğruluğu veya tüm veri setinin kalitesi olarak yorumlamıyorum.

`other` kategorisinde **61,125** kayıt (**%49.09**) bulunması, sınıflandırıcının geliştirilmesi gerektiğine işaret etmektedir.

## Sürüm farkı ve tamamlanmamış çalışmalar

Bu iki analiz 124.510 QA üzerinde yapıldı. Sonraki kalite aşamasında 14 kayıt geçici olarak bekletildi ve 124.496 QA içeren ayrı bir çalışma kopyası oluşturuldu. Buradaki dil ve görev dağılımı sonuçlarını 124.496 QA için yeniden hesaplanmış sonuçlar gibi sunmuyorum.

Bağımsız insan doğrulaması, görev sınıflandırıcısının iyileştirilmesi ve güncel çalışma kopyasındaki dağılımların yeniden değerlendirilmesi tamamlanmamıştır.

## Veri kullanım ve eğitim onayı

- `training_approved = false`
- `rights_status = pending_review`

## Kanıt dosyaları

- `reports/statistics/language_quality_report_v0.9.1.json`
- `reports/statistics/instruction_task_quality_v0.9_2.json`
- `reports/statistics/language_quality_report_v0.9.1.md`
- `reports/statistics/instruction_task_quality_v0.9_2.md`
- `reports/quality/instruction_end_to_end_accounting_v0.9.json`

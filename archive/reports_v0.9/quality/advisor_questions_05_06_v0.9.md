# LexiTech TR — Danışman Soruları 5 ve 6

**Proje:** Türkçe Hukuk Teknolojileri Asistanı
**Kapsam:** Veri temizleme, eleme ve teknik doğrulama
**Sürüm:** v0.9

## 5. Veri temizleme işlemlerini nasıl gerçekleştirdim?

LexiTech TR projemde veri hazırlama sürecini Instruction Dataset ve Domain Corpus olmak üzere iki ayrı veri akışı üzerinden yürüttüm.

### Instruction Dataset

İki Hugging Face kaynağından toplam **378.903** soru-cevap kaydı topladım. Kayıtları ortak şemaya dönüştürdükten sonra HTML karakterlerini çözdüm, HTML etiketlerini temizledim, Unicode NFC normalizasyonu uyguladım ve gereksiz boşlukları düzenledim.

İlk temizlemede cevabı boş olan **1 kaydı** ayırdım. Bu kaydın sinanelms/hukukisorular kaynağında 91.350. satırdan geldiğini ve cevap uzunluğunun sıfır olduğunu kayıt düzeyinde doğruladım.

Temizleme sonrasında **378.902** kayıt kaldı. Temizlenmiş soru ve cevap içeriği üzerinden SHA-256 özeti hesaplayarak **70.893** birebir tekrarı ayırdım ve **308.009** benzersiz kayıt elde ettim. Kalan kayıtların saklanan SHA-256 özetlerini yeniden hesaplayarak hash bütünlüğünü doğruladım.

Daha sonra Instruction aday seçimi, kaynak ve atıf inceleme karantinaları, alternatif cevap ayrımı, splitler arası leakage düzeltmesi ve ön kalite incelemesini uyguladım. Böylece **124.496** kayıtlık geçici kalite bekletmeli çalışma kopyasına ulaştım.

### Domain Corpus

Domain Corpus kapsamında **12 kanuna** ait PDF dosyalarını kullandım. PDF metin çıkarımından sonra sayfa başlıklarını temizledim, Unicode NFC normalizasyonu, özel boşluk ve birleşik karakter düzeltmeleri ile metin boşluğu düzeltmeleri uyguladım.

Ham PDF dosyalarının ve son temiz metinlerin SHA-256 özetlerini envanterle karşılaştırdım. **12 PDF ve 12 temiz metnin tamamı** doğrulamadan geçti. Son korpustaki 12 metnin de seçilen temiz metin dosyalarıyla birebir eşleştiğini kontrol ettim.

Hukuki metinleri parçalamak için original, sentence-aware ve legal-aware olmak üzere üç yöntem geliştirdim. Son veri seti dokümantasyonunda legal-aware sürümünü referans aldım. Üç yöntemde de maksimum 2.048 token sınırını sağladım.

## 6. Hangi verileri, neden eledim?

Veri eleme işlemlerini gerekçelerine göre birbirinden ayırdım. Seçim dışı bırakılan veya karantinaya alınan kayıtların tamamını hatalı ya da kalıcı olarak silinmiş kabul etmedim.

### Instruction Dataset kayıt muhasebesi

| İşlem | Girdi | Ayrılan | Kalan |
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

İlk kayıt, cevabı boş olduğu için ayrıldı. 70.893 kayıt birebir tekrar olarak belirlendi. 176.964 kayıt ise Instruction aday seçim koşullarını karşılamadığı için aday havuzuna alınmadı; bu sonuç kayıtların hukuken yanlış olduğu anlamına gelmemektedir.

Atıf incelemesi gereken 933 ve kaynak belgesi incelemesi gereken 960 kaydı karantinaya ayırdım. Alternatif cevap grubundaki 4.630 kaydı ayrıca değerlendirilmek üzere ayırdım. Aynı cevaplı 7 tekrar ve splitler arası sızıntıyla ilişkili 5 kayıt için veri ayrımı uyguladım.

Son kalite taramasında 2.678 heuristik inceleme adayı tespit edildi. Bu sayı kesin hatalı kayıt sayısı değildir. Bunlar arasından 14 kaydı geçici olarak beklettim. Bu 14 kayıt hakkında nihai insan değerlendirmesi henüz yapılmadı.

### Domain Corpus

Domain Corpus'taki 12 kanunun tamamını korudum. Farklı chunking yöntemlerinde üretilen parça sayıları şöyledir:

| Yöntem | Train | Validation | Test | Toplam |
|---|---:|---:|---:|---:|
| original | 881 | 40 | 59 | 980 |
| sentence_aware | 884 | 40 | 59 | 983 |
| legal_aware | 889 | 40 | 59 | 988 |

Bu farklılıklar veri silinmesini değil, parçalama stratejilerinin farklı sınırlar oluşturmasını göstermektedir.

Legal-aware sürümündeki **988 chunk'ın tamamı** manuel inceleme beklemektedir. Dosya hash doğrulaması ve teknik chunk bütünlüğü, hukuki doğruluğu tek başına kanıtlamaz.

## Açık kalan çalışmalar

- Kaynak kullanım haklarının doğrulanması
- Kanun metinlerinin güncellik ve sürüm kontrolü
- Hukuki içeriklerin bağımsız uzman incelemesi
- QA inceleme adaylarının insan tarafından değerlendirilmesi
- Legal-aware chunk'ların manuel kontrolü
- Hukuk alanlarına göre kapsam ve kalite analizinin tamamlanması

## Veri kullanımı ve eğitim onayı

Bu aşamada model eğitimi için veri kullanım onayı verilmiş değildir.

- `training_approved = false`
- `rights_status = pending_review`

## Kanıt dosyaları

- `reports/quality/instruction_end_to_end_accounting_v0.9.json`
- `reports/quality/domain_cleaning_and_exclusion_v0.9.json`
- `reports/quality/domain_cleaning_integrity_v0.9.json`
- `reports/quality/domain_chunk_final_comparison_v0.9.json`
- `reports/sources/legislation_documents.csv`

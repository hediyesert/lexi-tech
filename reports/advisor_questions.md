# Danışmana sorulacaklar (taslak)

Bu metin taslaktır, henüz gönderilmedi. Grup bilgilerini ekleyip kendi adınızla gönderin.

---

**Konu:** LexiTech TR, veri kullanım hakları hakkında görüşünüz

Sayın [danışman adı],

LexiTech TR vize çalışmasında iki veri seti hazırladık: 12 kanundan oluşan Domain Corpus ve 4.000 örneklik Instruction
Dataset. Teknik hazırlık tamamlandı, ancak kullanım hakları doğrulanmadığı için veri setlerini eğitime onaylı olarak
işaretlemedik. Şu dört konuda görüşünüzü rica ediyoruz.

**1. Kanun metinleri.** 12 kanunu mevzuat.gov.tr'den aldık. İkincil kaynaklara göre FSEK m. 31, resmen yayımlanan
mevzuat ve yargı içtihatlarının kullanımını serbest bırakıyor. Bu hükme dayanarak metinleri model eğitiminde kullanabilir
ve veri setini teslim edebilir miyiz? Mevzuat Bilgi Sistemi'nin kullanım koşullarının ayrıca kısıt getirip getirmediğini
kontrol etmemiz gerekir mi?

**2. `sinanelms/hukukisorular`.** Örneklerimizin 3.316'sı bu Hugging Face veri setinden geliyor. Veri setinin kartında lisans
beyanı yok. Yayıncıya göre hukuk makalelerinden Gemini 2.5 Pro ile üretilmiş, kaynak olarak 8 hukuk sitesi bildirilmiş.
Bu kayıtları akademik proje kapsamında kullanabilir miyiz? Yayıncıdan veya sitelerden izin istememiz gerekir mi?

Kullanamazsak bu 3.316 örneğin yerine kanun metninden yeni örnekler üretmemiz gerekir. Geri kalan 684 örnek (kural
tabanlı, elle yazılmış ve Apache-2.0 beyanlı) bu karardan etkilenmez. Ancak bu, setin büyük bölümünü yeniden
hazırlamak demektir ve vize takvimini etkiler.

**3. Hukuki doğrulama.** Cevaplar kanun metniyle otomatik karşılaştırıldı, ama bu hukuki doğruluğu kanıtlamıyor. Test
kümesinden bir örneklemi inceleyebilecek bir hukukçu önerebilir misiniz? 

**4. İnsan kalite kontrolü.** Rehberdeki manuel kontrolü vize teslimine kadar yapamadık. Örnekler yalnızca yapay zekâ
asistanıyla ön incelemeden geçti: 200 instruction örneğinin 170'i okundu, 150 domain parçası otomatik tarandı. Bu insan
onayı değildir ve raporda böyle belirtilmiştir. İnceleme dosyası hazır. Bu eksiği final döneminin başında tamamlamamız
uygun olur mu?

**Ek bir soru: sürüm adı.** Rehber Dataset v1.0 teslimi istiyor. Hak ve insan incelemesi tamamlanmadan veri setlerini
`v1.0-rc1` olarak sunmak uygun mu, yoksa teslim için v1.0 adı mı beklenir?

Saygılarımızla,
[ad soyad], [ad soyad], [ad soyad]

---

## Grup için not

Kanıtlar: `reports/sources/source_rights_audit_v0.9.csv`, `reports/sources/hf_license_evidence_v0.9.csv`,
`archive/reports_v0.9/quality/advisor_source_rights_v0.9.md`.

FSEK m. 31 bilgisi ikincil kaynaklardan alındı. Metnin güncel halini mevzuat.gov.tr'den kontrol edin. Kaynak örneği:
[Anayasa Mahkemesi norm denetimi kararı](https://normkararlarbilgibankasi.anayasa.gov.tr/Dosyalar/Kararlar/KararPDF/2014-135-nrm.pdf).

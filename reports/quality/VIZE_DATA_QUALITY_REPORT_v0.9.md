# LexiTech TR — Vize Veri Kalitesi Raporu

**Rapor sürümü:** v0.9
**Tarih:** 2026-10-27
**Çalışma alanı:** Türkçe hukuk yapay zekâsı
**Aşama:** Veri mühendisliği ve kalite denetimi

## 1. Yönetici özeti

Bu çalışma, Türkçe hukuk alanında kullanılabilecek iki
veri setinin teknik ön taslaklarını hazırlamıştır:

1. **Domain Corpus v0.9:** Resmî mevzuat metinlerinden
   oluşturulan alan korpusu.
2. **Instruction Dataset v0.9:** Türkçe hukuk
   soru-cevap kayıtlarından oluşturulan SFT aday havuzu.

**Bu aşamada model eğitimi yapılmamıştır.**

Teknik veri hazırlama ve bazı otomatik bütünlük kontrolleri
tamamlanmış olsa da, kaynak kullanım hakları, kapsamlı
insan değerlendirmesi ve hukuk uzmanı doğrulaması
tamamlanmamıştır.

Bu nedenle iki veri seti de henüz eğitim için
onaylanmış `v1.0` sürümü değildir.

## 2. Domain Corpus sonuçları

| Ölçüt | Sonuç |
|---|---:|
| Kanun belgesi | 12 |
| Farklı kanun numarası | 12 |
| Karakter | 4.471.279 |
| Qwen tokenizer tokenı | 1.655.887 |

**Kanun numaraları:** 2004, 213, 2577, 2709, 4721, 4857, 5237, 5271, 5510, 6098, 6102, 6502

Korpusun belge bazlı train/validation/test dosyaları
ve hukuki duyarlı chunk sürümü hazırlanmıştır.

İlgili dosyalar:

- `data/final/domain_corpus_v0.9_tokenized.jsonl`
- `data/final/domain_v0.9/`
- `data/final/domain_v0.9/chunks_legal_aware/`
- `DATASET_CARD.md`

### Domain Corpus sınırlamaları

- PDF'den metin çıkarımına bağlı hatalar bulunabilir.
- Kanunların güncelliği ve yürürlükteki sürümleri
  ayrıca karşılaştırılmalıdır.
- Değişiklik tabloları doğrudan eğitim verisi
  kabul edilmemelidir.
- Validation/test ayrımı hukuk alanları açısından
  yeterince temsili değildir.
- Kapsamlı manuel kalite kontrolü tamamlanmamıştır.

## 3. Instruction Dataset hazırlama süreci

| İşlem | Kayıt |
|---|---:|
| İlk iki kaynak toplamı | 378.903 |
| Birebir tekrar sonrası ilk havuz | 308.009 |
| Madde göstergeli aday havuzu | 131.045 |
| Atıf incelemesine ayrılan | 933 |
| Kaynak bilgisi nedeniyle ayrılan OrionCAF adayı | 960 |
| İlk bölünmüş veri seti | 129.152 |
| Farklı cevaplı soru versiyonları (inceleme havuzu) | 4.630 |
| Eşdeğer soru-cevap tekrarı | 7 |
| Kümeler arası normalize soru tekrarı | 5 |
| **Güncel ön taslak** | **124.510** |

Bu kayıtların ayrılması, içeriklerinin kesin olarak
yanlış olduğuna ilişkin bir karar değildir.

### Güncel train/validation/test sayıları

| Küme | Kayıt |
|---|---:|
| Train | 111.782 |
| Validation | 6.397 |
| Test | 6.331 |
| **Toplam** | **124.510** |

### Kanun bazında dağılım

| Kanun | Train | Validation | Test | Toplam |
|---|---:|---:|---:|---:|
| 2004 | 3.208 | 118 | 39 | 3.365 |
| 213 | 852 | 53 | 89 | 994 |
| 2577 | 4.509 | 288 | 152 | 4.949 |
| 2709 | 2.037 | 104 | 118 | 2.259 |
| 4721 | 11.714 | 387 | 183 | 12.284 |
| 4857 | 2.843 | 62 | 1 | 2.906 |
| 5237 | 47.206 | 2.959 | 4.221 | 54.386 |
| 5271 | 27.568 | 2.097 | 1.365 | 31.030 |
| 5510 | 1.580 | 18 | 8 | 1.606 |
| 6098 | 8.738 | 254 | 128 | 9.120 |
| 6102 | 1.201 | 54 | 24 | 1.279 |
| 6502 | 326 | 3 | 3 | 332 |

### Veri bölme ve sızıntı kontrolleri

- Kaynak dosyası temelli bölme uygulanmıştır.
- Güncel kümeler arasında ortak kaynak dosyası: **0**.
- Kontrol edilen normalize soru metnine göre
  kümeler arası birebir tekrar: **0**.
- İlk bölme bütünlük kontrolü: **PASS**.
- Sızıntı düzeltme kontrolü: **PASS**.

**Sınırlama:** Aynı anlama gelen fakat farklı
kelimelerle yazılmış bütün soruların tespit edildiği
iddia edilmemektedir.

### Yakın tekrar denetimi

Önceki MinHash analizi 308.009 kayıt üzerinde
yürütülmüştür. Yöntem soru ve cevap metnini birlikte
karşılaştırmış, üç kelimelik shingles ve 0,85
Jaccard eşiği kullanmıştır.

Güncel veri setinde, önceki rapordaki çiftlerden:

- İki kaydı da kalan çift: **527**
- Aynı split içinde kalan çift: **527**
- Farklı splitlerde kalan çift: **0**

Bu sonuçlar **yalnızca eski MinHash raporunda
tespit edilmiş çiftler** için geçerlidir.
Güncel soru metinleri üzerinde kapsamlı yeni bir
yakın tekrar taraması yapılmamıştır.

### Dengeli değerlendirme sınırlaması

İş Kanunu, sosyal sigortalar, ticaret ve tüketici
hukuku için validation/test örneği sayıları
düşüktür. Özellikle küçük test gruplarından
güvenilir kanun bazlı performans sonucu
çıkarılmamalıdır.

## 4. Madde atıfları ve hukuki doğruluk

İlk aday havuzunda otomatik olarak incelenen
kayıt sayısı: **131.045**.

Madde numarası yapısal kontrolde:

- Hedef kanun metninde numaraları bulunan:
  **130.112**
- Ek atıf incelemesi gerektiren:
  **933**

Madde numarasının bir kanunda bulunması,
cevabın doğru, güncel veya uygun biçimde
kaynaklandırılmış olduğunu kanıtlamaz.

Bazı cevaplarda farklı kanunlara yapılan
atıflar veya başka bir kanun numarasının
madde numarası olarak algılanması söz konusudur.

## 5. Manuel kalite değerlendirmesi

Örneklem dosyası:

`reports/quality/instruction_manual_review_200_v0.9.csv`

Toplam örnek: **200**.

| Manuel inceleme durumu | Kayıt sayısı |
|---|---:|
| manual_review_required | 1 |
| pending | 198 |
| provisional_accept | 1 |

İlk iki kayda ilişkin değerlendirmeler **ön niteliktedir**.
Nihai hukuk uzmanı onayı verilmemiştir.

Örneklem kanun bazında tabakalı olarak oluşturulmuştur.
Bu nedenle doğrudan tüm veri setinin hata oranını
tahmin eden temsili bir rastgele örneklem
olarak kullanılmamalıdır.

## 6. Kaynak ve kullanım hakları

Kaynak hakları denetim dosyası:

`reports/sources/source_rights_audit_v0.9.csv`

Toplam kayıtlı kaynak girdisi: **22**.

| Kaynak türü | Kayıt sayısı |
|---|---:|
| official_legislation | 12 |
| reported_upstream_website | 8 |
| third_party_qa_dataset | 2 |

Eğitim için açıkça onaylanmış kaynak sayısı:
**0**.

Instruction Dataset içinde:

- `training_approved: false`:
  **124.510** kayıt.
- `rights_status: pending_review`:
  **124.510** kayıt.

Bir kaynak için onay kaydı bulunmaması,
kullanımın kesinlikle yasak olduğunu göstermez.
İzin durumu henüz yeterli kanıtla
doğrulanmamıştır.

Kaynakların yayımlanan lisans beyanları ile
altta yatan metinlerin hakları ayrı
değerlendirilmelidir.

## 7. Bilinen riskler

1. Hukuki doğruluk ve güncellik hataları.
2. Yanlış veya doğrulanmamış kanun-madde atıfları.
3. Kaynağı doğrulanmamış yargı kararı atıfları.
4. Yakın anlamlı soru tekrarlarının devam etmesi.
5. Ceza hukuku ağırlıklı veri dağılımı.
6. Yetersiz hukuk alanı temsili olan test kümeleri.
7. PDF/OCR kaynaklı metin bozulmaları.
8. Telif ve kullanım izinlerinin tamamlanmamış olması.
9. Kişisel veri taramasının ayrıca yapılması gerekliliği.
10. Manuel uzman kontrolünün büyük ölçüde beklemesi.

## 8. Vize sonrası / v1.0 öncesi işler

- [ ] Domain Corpus'tan 100–200 belgenin veya uygun
      değerlendirme biriminin manuel örnek incelemesi.
- [ ] Instruction Dataset'ten 150–200 örneğin
      planlı manuel kalite değerlendirmesi.
- [ ] Kanunların güncel metinlerle karşılaştırılması.
- [ ] Üçüncü taraf veri kaynaklarının lisans ve
      izin kanıtlarının tamamlanması.
- [ ] Kişisel veri ve hassas içerik kontrolü.
- [ ] Soru odaklı yakın tekrar / sızıntı analizi.
- [ ] Eksik hukuk alanları için güvenilir
      değerlendirme örneklerinin artırılması.
- [ ] Kalite sorunları giderildikten sonra
      nihai eğitim adaylarının belirlenmesi.
- [ ] `v1.0` veri seti kartlarının güncellenmesi.

## 9. İlgili belgeler

- `DATASET_CARD.md`
- `INSTRUCTION_CARD.md`
- `reports/sources/source_rights_audit_v0.9.csv`
- `reports/quality/instruction_split_integrity_v0.9.json`
- `reports/quality/instruction_dedup_report_v0.9.json`
- `reports/quality/instruction_balance_audit_v0.9.json`
- `reports/quality/instruction_leakage_fix_v0.9.json`
- `reports/quality/instruction_existing_near_duplicates_v0.9.json`
- `reports/quality/instruction_manual_review_200_v0.9.csv`

## 10. Sonuç

LexiTech TR vize aşamasında iki farklı amaç için
veri hazırlama altyapısı oluşturulmuştur.

**Teknik kazanım:** Ayrı veri setleri, metadata,
token sayımı, bölümleme, tekrar kontrolleri,
kaynak bazlı split ve denetim raporları.

**Henüz tamamlanmayan:** İnsan ve hukuk uzmanı
onayı, lisans kanıtları, güncellik doğrulaması
ve kapsamlı anlamsal yakın tekrar denetimi.

Bu çalışma, tamamlanmış ve eğitim için onaylanmış
bir hukuk modeli veya nihai `v1.0` veri seti
olarak sunulmamaktadır.

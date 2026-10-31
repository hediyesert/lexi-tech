# LexiTech TR - Experiment Log

Bu dosya LexiTech TR projesinin veri hazırlama sürecinde gerçekleştirilen
deneyleri, kullanılan yöntemleri, elde edilen sonuçları ve alınan metodolojik
kararları kayıt altına almak amacıyla oluşturulmuştur.

---

## 1. Dataset Acquisition

LexiTech TR için ilk veri kaynağı olarak Hugging Face üzerinde bulunan iki
Türkçe hukuk veri seti kullanıldı:

- sinanelms/hukukisorular
- OrionCAF/turkish_law_qa_dataset

Kayıt sayıları:

- sinanelms/hukukisorular: 360,598
- OrionCAF/turkish_law_qa_dataset: 18,305
- Toplam ham kayıt: 378,903

Ham veriler `data/raw/` altında JSONL formatında saklandı.

Ham veri katmanı immutable olarak kabul edildi ve sonraki veri işleme
aşamalarında doğrudan değiştirilmedi.

Ham dosyaların bütünlük kontrolü için SHA-256 manifest oluşturuldu.

---

## 2. Schema Extraction

Script:

`02_extract.py`

Farklı şemalara sahip veri kaynakları ortak bir veri yapısına dönüştürüldü.

Ortak alanlar:

- id
- source
- source_split
- source_row
- source_document
- question
- answer
- metadata

Her kayıt için provenance bilgisinin korunmasına dikkat edildi.

Extraction sonucu:

- Input: 378,903
- Output: 378,903

Bu aşamada herhangi bir kayıt silinmedi.

---

## 3. Extracted Dataset Validation

Extraction sonrasında veri doğrulama işlemi gerçekleştirildi.

Kontrol edilen başlıca durumlar:

- Invalid JSON
- Eksik alan
- Null question
- Null answer
- Empty question
- Empty answer
- Invalid ID
- Duplicate ID

Sonuçlarda bozuk JSON veya temel şema problemi tespit edilmedi.

`sinanelms/hukukisorular` veri setinde 1 adet boş cevap bulundu.

Ayrıca veri setlerinde önemli miktarda duplicate kayıt bulunduğu gözlemlendi.

---

## 4. Data Cleaning

Script:

`03_clean.py`

Uygulanan işlemler:

- HTML entity temizleme
- HTML tag temizleme
- Unicode NFC normalization
- Whitespace normalization
- Boş soru veya cevap içeren kayıtların kaldırılması

Sonuç:

- Input: 378,903
- Kept: 378,902
- Removed: 1
- Changed: 15,091

Temizleme aşamasında yalnızca 1 geçersiz kayıt kaldırıldı.

---

## 5. Exact Duplicate Analysis

Script:

`04_analyze_duplicates.py`

Exact duplicate tespiti için temizlenmiş:

`question + answer`

içeriği üzerinden SHA-256 hesaplandı.

Kaynak adı hash hesabına dahil edilmedi. Böylece farklı veri kaynaklarında
bulunabilecek aynı içeriklerin de tespit edilmesi amaçlandı.

Sonuç:

- Toplam temiz kayıt: 378,902
- Unique content: 308,009
- Exact duplicate: 70,893
- Cross-source exact duplicate: 0

---

## 6. Exact Deduplication

Script:

`05_exact_deduplicate.py`

Aynı SHA-256 içerik hash değerine sahip kayıtlardan ilk karşılaşılan kayıt
korundu.

Sonuç:

- Input: 378,902
- Removed: 70,893
- Exact-unique output: 308,009

Bağımsız doğrulama sonucunda:

- Total records: 308,009
- Unique SHA-256: 308,009
- Duplicate SHA-256: 0
- Missing content hash: 0

elde edildi.

---

## 7. MinHash / LSH Pilot Experiment

Script:

`06_minhash_analyze.py`

Exact duplicate olmayan fakat yüksek derecede benzer kayıtların bulunması için
MinHash ve Locality Sensitive Hashing (LSH) yöntemi test edildi.

Parametreler:

- Tokenization: lowercase Unicode word tokens
- Shingle size: 3 words
- MinHash permutations: 128
- LSH threshold: 0.85

İlk 5,000 kayıt üzerinde pilot çalışma gerçekleştirildi.

Sonuç:

- Analiz edilen kayıt: 5,000
- LSH candidate pair: 4
- Gerçek Jaccard >= 0.85: 3

LSH tarafından bulunan bir adayın gerçek Jaccard değeri yaklaşık 0.8214
olduğu için near-duplicate olarak kabul edilmedi.

Bu deney sonucunda LSH çıktılarının doğrudan duplicate kabul edilmemesine,
adayların gerçek shingle Jaccard similarity ile doğrulanmasına karar verildi.

---

## 8. Full Corpus MinHash / LSH Analysis

Script:

`07_minhash_full.py`

Pilot deney başarılı olduktan sonra yöntem 308,009 exact-unique kaydın
tamamına uygulandı.

Bellek kullanımını azaltmak için işlem çok geçişli ve streaming ağırlıklı
olarak tasarlandı.

### Pass 1

Dataset streaming olarak okunarak MinHash imzaları üretildi ve LSH ile aday
çiftler bulundu.

### Pass 2

Yalnızca LSH adaylarında yer alan kayıtlar toplandı.

### Pass 3

LSH adaylarının gerçek 3-word-shingle Jaccard similarity değerleri
hesaplandı.

Sonuç:

- Input records: 308,009
- LSH candidate pairs: 3,091
- Verified Jaccard >= 0.85 pairs: 2,688
- LSH candidate olup doğrulamayı geçemeyen: 403
- Cross-source verified near-duplicate pairs: 0

Bu aşamada hiçbir kayıt silinmedi.

---

## 9. Near-Duplicate Similarity Analysis

Script:

`08_analyze_near_duplicates.py`

Doğrulanmış 2,688 near-duplicate çift üzerinde ek analiz gerçekleştirildi.

Sonuç:

- Verified pair: 2,688
- Etkilenen benzersiz kayıt: 5,097
- Minimum Jaccard: 0.850000
- Maximum Jaccard: 1.000000
- Average Jaccard: 0.937218

Jaccard dağılımı:

- 0.85 - <0.90: 530
- 0.90 - <0.95: 1,012
- 0.95 - <1.00: 915
- 1.00: 231

Ek olarak:

- Aynı soruya sahip çift: 1,458
- Aynı cevaba sahip çift: 1,055

Jaccard = 1.0 olması, kayıtların string/byte seviyesinde exact duplicate
olduğu anlamına gelmemektedir. Jaccard karşılaştırması normalize edilmiş
3-word-shingle kümeleri üzerinde gerçekleştirilmektedir.

---

## 10. Near-Duplicate Cluster Analysis

Script:

`09_analyze_duplicate_clusters.py`

Near-duplicate çiftlerin birbirleriyle ilişkisini incelemek için connected
component mantığında cluster analizi gerçekleştirildi.

Sonuç:

- Verified near-duplicate pairs: 2,688
- Cluster içindeki unique records: 5,097
- Total clusters: 2,494
- Largest cluster: 6 records

Cluster size distribution:

- 2 kayıtlı cluster: 2,410
- 3 kayıtlı cluster: 64
- 4 kayıtlı cluster: 16
- 5 kayıtlı cluster: 3
- 6 kayıtlı cluster: 1

Eğer her cluster'dan yalnızca bir kayıt korunsaydı teorik olarak 2,603 kayıt
çıkarılabilirdi.

Ancak bu değer otomatik olarak silinecek kayıt sayısı olarak kabul edilmedi.

---

## 11. Near-Duplicate Deduplication Decision

Near-duplicate kayıtların bu aşamada otomatik olarak silinmemesine karar
verildi.

Gerekçe:

Hukuki metinlerde küçük metinsel farklılıklar önemli semantik ve hukuki
farklılıklara neden olabilir.

Örneğin:

- süre farklılıkları,
- parasal miktarlar,
- kanun/madde numaraları,
- olumlu/olumsuz ifadeler,
- "yapabilir" / "yapamaz" gibi modal farklılıklar

metinlerin lexical olarak yüksek benzerlik göstermesine rağmen farklı hukuki
sonuçlara sahip olmasına neden olabilir.

Bu nedenle MinHash + LSH aşaması otomatik silme mekanizması olarak değil,
near-duplicate detection ve quality-control mekanizması olarak kullanılacaktır.

Mevcut karar:

- Exact duplicates: kaldırıldı.
- Near duplicates: tespit edildi ve raporlandı.
- Near duplicates: otomatik olarak kaldırılmadı.
- Sonraki veri hazırlama aşamalarında gerekli durumlarda manuel veya
  semantik kontrollü değerlendirme yapılacaktır.

---

## 12. Current Pipeline Status

Mevcut veri pipeline'ı:

378,903 RAW

→ 378,903 EXTRACTED

→ 378,902 CLEANED

→ 308,009 EXACT UNIQUE

→ 3,091 LSH CANDIDATE PAIRS

→ 2,688 VERIFIED NEAR-DUPLICATE PAIRS

→ 2,494 NEAR-DUPLICATE CLUSTERS

Exact-unique corpus mevcut durumda 308,009 kayıttan oluşmaktadır.

Near-duplicate analizi corpus üzerinde herhangi bir otomatik kayıt silme
işlemi gerçekleştirmemiştir.

---

## 13. Vize Rehberi Karşılaştırması (31.10.2026)

Vize Rehberi ile v0.9 karşılaştırıldı. Ana bulgular:

- Instruction seti 124.510 kayıt, rehber kontrollü 3-5 bin örnek istiyor. Görev türlerinin %49'u `other`,
  sınır davranışı örneği yok, `source_document` bir kanun belgesine değil batch dosyasına bağlı.
- PDF çıkarma script'i yok, 8 temizleme script'i kaydı tutulmamış argümanlarla çalışmış.
- Domain kayıtlarında URL boş, `publication_year` ve `subtopic` yok, 3 chunk sürümü yan yana duruyor.
- Manuel incelemede 200 kayıttan 2'si bakılmış.

Karar: v0.9 havuzunu düzeltmek yerine, birebir tekrardan arındırılmış havuzdan yeniden seçim yapılacak.

## 14. Extraction Aracı Tespiti (31.10.2026)

PyMuPDF, pdfplumber ve pypdf, mevcut `data/extracted/legislation` dosyalarıyla karşılaştırıldı.

- pypdf, sayfalar `\n\n` ile birleştirildiğinde 12 dosyanın 12'sini bayt düzeyinde üretti.
- PyMuPDF her dosyada farklı sonuç verdi.

Karar: pypdf `02b_extract_legislation.py` içinde kullanılacak. 1.540 sayfanın hepsinde metin katmanı var, OCR gerekmedi.

## 15. Tek Temizleme Script'i (31.10.2026)

Sayfa başlığı silme, NFC ve `ğ` boşluğu düzeltmesi tek fonksiyonda birleştirildi.

- 12 kanunun 11'i v0.9 temiz metniyle bayt düzeyinde aynı çıktı.
- 5510 farklı: yalnızca o kanunda `ş` önündeki boşluk düzeltilmişti.
- Aynı hata diğer 11 kanunda duruyordu (`Ba şbakan`, `ki şilik`).

Karar: Sözlük tabanlı onarım tüm kanunlara uygulanacak. Boşluk dışı karakterin değişmediği hash ile doğrulanacak.

## 16. Kanıt Filtresi (31.10.2026)

Her soru-cevabın atıf yaptığı madde metni bulundu, cevap kelimelerinin maddede geçme oranı ölçüldü.

- Girdi 308.009, aday 31.962.
- En büyük eleme nedeni doğrulanamayan içtihat atfı (78.837), sonra cevaptaki site adresi (62.102).

Karar: Corpus'ta karar metni olmadığı için içtihat atıfları dışarıda kalacak. Hedefteki yargı kararı desteği
için ayrı karar kaynağı gerekiyor.

## 17. Görev Türleri ve Sınır Örnekleri (31.10.2026)

Kaynak veri setinde bulunmayan üç örnek türü eklendi:

- `madde_bulma`: 351 örnek, kanun başlıklarından kuralla üretildi, doğruluğu metinden garantili.
- `bilgi_yetersizligi`: 229 örnek. Olmayan madde, doğrulanamayan karar, kapsam dışı kanun, kişiye özel tahmin.
- `alan_disi`: 42 örnek, elle yazıldı.

Karar: Görev türü başına tavan %20, kanun başına tavan %20. Sonuç 4.000 örnek.

## 18. İlk Kalite Turu (31.10.2026)

Asistan ön incelemesi yapıldı, insan onayı değildir.

- Domain: 150 chunk'ın başı ve sonu okundu. Harf aralıklı metin ve kopuk baş harf bulundu, temizleme düzeltildi.
- Instruction: 60 kaynaklı kayıt maddesiyle karşılaştırıldı. 3 kayıt reddedildi (site adresi, karar numarası,
  LLM notu), 1 kayıt hukukçuya bırakıldı.

Karar: Tekil silme yerine aynı türü yakalayan kurallar eklendi. `source_artifact` kuralı 62.102 kayıt eledi.
`neden_sonuc` kuralı daraltıldı, çünkü `nedeni` ve `sebebi` kelimeleri 60 kayıtta 4 yanlış etikete yol açtı.

## 19. Pipeline Sadeleştirme (31.10.2026)

95 script 13 adımlı pipeline ve yardımcı dosyalarla toplam 15 dosyaya indi, eskiler `archive/` altına taşındı. `run_pipeline.py` ve 14 otomatik test eklendi.
Domain v1.0 `reports/sources/domain_sections_v1.0.csv` dosyasıyla v0.9 ara dosyalarından bağımsız hale getirildi.

## 20. İnsan İncelemesi Hazırlığı (31.10.2026)

Domain örneklemi son temizlik turundan önce çekildiği için chunk kimlikleri kaymıştı: 150 kimlikten 1'i bulunamadı,
kalanların metni değişmiş olabilirdi.

Karar: İlk asistan turu `qc_domain_assistant_round1_v1.0.csv` olarak ayrıldı, insan incelemesi için güncel veriden yeni
150 chunk çekildi. Excel dosyası cevabı kaynak maddeyle yan yana gösterir, `qc_review_sheet.py import` sonuçları geri alır.

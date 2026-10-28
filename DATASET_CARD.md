# LexiTech TR — DATASET_CARD

**Sürüm:** Domain Corpus v0.9 (ön taslak)
**Belge tarihi:** 2026-10-27
**Dil:** Türkçe
**Alan:** Türkiye hukuku
**Durum:** Hukuki içerik ve kullanım hakları için nihai onay bekleniyor.

## 1. Amaç

Türkçe hukuk alanına uyarlanacak dil modelleri için
alan korpusu oluşturmak. Bu korpus ileriki aşamada
CPT/DAPT çalışmaları için aday veri sağlayabilir.

**Vize aşamasında model eğitimi gerçekleştirilmemiştir.**

## 2. Veri kapsamı

- Belge sayısı: **12**
- Toplam karakter: **4,471,279**
- Toplam tokenizer tokenı: **1,655,887**
- Kaynak türü: Resmî mevzuat PDF belgelerinden çıkarılan metinler.
- Tokenizer: `Qwen/Qwen2.5-3B-Instruct`.
- Birim: Kanun belgesi; ayrıca parçalama (chunking)
  sürümleri hazırlanmıştır.

### Kapsanan kanunlar

- **2004:** İcra ve İflas Kanunu
- **213:** Vergi Usul Kanunu
- **2577:** İdari Yargılama Usulü Kanunu
- **2709:** Türkiye Cumhuriyeti Anayasası
- **4721:** Türk Medeni Kanunu
- **4857:** İş Kanunu
- **5237:** Türk Ceza Kanunu
- **5271:** Ceza Muhakemesi Kanunu
- **5510:** Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu
- **6098:** Türk Borçlar Kanunu
- **6102:** Türk Ticaret Kanunu
- **6502:** Tüketicinin Korunması Hakkında Kanun

## 3. Veri kaynakları ve izlenebilirlik

Kaynak listesi:

`reports/sources/legislation_documents.csv`

Bu listede mevcut kaynak bilgileri, erişim tarihleri ve
SHA-256 değerleri saklanmaktadır.

Resmî mevzuat PDF'lerinin kullanılmış olması, her türlü
yeniden dağıtım veya model eğitimi için kullanım haklarının
otomatik olarak onaylandığı anlamına gelmez.

**Kullanım hakları durumu: İnceleme bekliyor.**

## 4. Veri hazırlama işlemleri

1. PDF belgelerinin temin edilmesi.
2. Metin çıkarımı ve otomatik metin temizliği.
3. Belge kimliği, kaynak ve SHA-256 metadata'sının kaydı.
4. Tokenizer ile token sayılarının hesaplanması.
5. Belge bazlı train/validation/test ayrımı.
6. Ana kanun, işlenmemiş hükümler ve değişiklik
   tablolarına yönelik bölümleme.
7. Token sınırını gözeten hukuki duyarlı parçalama.
8. Parça bütünlüğü ve yakın tekrar denetimleri.

## 5. Bölme yaklaşımı

Kanun belgeleri belge düzeyinde ayrılmıştır.

- Train belge sayısı: 10
- Validation belge sayısı: 1
- Test belge sayısı: 1

Bu ayrımda farklı splitlerde aynı kanun belgesi bulunmaz.

**Sınırlama:** Validation ve test kümeleri yalnızca
birer kanundan oluşmaktadır. Dolayısıyla tüm hukuk
alanlarını temsil eden dengeli bir değerlendirme
sağladıkları iddia edilemez.

## 6. Veri biçimi

- Belge düzeyi:
  `data/final/domain_corpus_v0.9_tokenized.jsonl`
- Belge splitleri:
  `data/final/domain_v0.9/`
- Hukuki duyarlı chunk splitleri:
  `data/final/domain_v0.9/chunks_legal_aware/`

Örnek metadata alanları:

`document_id`, `law_number`, `title`, `source_url`,
`raw_sha256`, `text_sha256`, `token_count`,
`rights_status`, `quality_status`.

## 7. Kalite ve bilinen riskler

- PDF çıkarımından kaynaklanabilen OCR, harf,
  kelime aralığı ve madde numarası hataları.
- Belge sürümlerinin güncelliğinin ayrıca
  doğrulanması gerekliliği.
- Değişiklik tablolarının model eğitimine doğrudan
  alınmaması gerekliliği.
- Hukuki duyarlı chunking işleminde bazı uzun
  maddelerin bölünmüş olması.
- Otomatik temizliğin hukuk uzmanı onayı yerine
  geçmemesi.
- Kaynak belgelerin güncel ve yürürlükteki metinlerle
  karşılaştırılmasının tamamlanmamış olması.

Chunk metadata'sındaki `requires_manual_review`
ve `training_candidate` alanları dikkate alınmalıdır.

## 8. Kalite kanıtları

- `reports/statistics/domain_token_summary_v0.9.json`
- `reports/quality/domain_chunk_final_comparison_v0.9.json`
- `reports/statistics/domain_chunk_stats_legal_aware_v0.9.json`
- `reports/quality/domain_section_plan_v0.9.csv`
- `reports/quality/domain_corpus_near_duplicate_pairs_v0.9.csv`

## 9. İnsan değerlendirmesi

Alan korpusu için hedeflenen kapsamlı manuel
örnek incelemesi ve nihai hukuki uzman onayı
henüz tamamlanmamıştır.

## 10. Kullanım sınırları

Bu veri seti **v0.9 teknik ön taslaktır**.

Kaynakların izin durumu, metin güncelliği, hukuki
doğruluk ve insan kalite değerlendirmesi tamamlanmadan
`v1.0` veya eğitim için onaylanmış veri olarak
sunulmamalıdır.

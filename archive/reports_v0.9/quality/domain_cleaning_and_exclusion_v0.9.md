# LexiTech TR — Domain Corpus Temizleme ve Eleme Raporu v0.9

**Danışman soruları:** 5 (temizleme) ve 6 (eleme gerekçeleri).

## 1. Kapsam

Domain Corpus, 12 kanuna ait PDF kaynaklarından hazırlanmıştır. 12 belgenin tamamı son korpusta korunmuştur. Bu bölümde QA Instruction Dataset değil, kanun metinleri incelenmektedir.

## 2. Temizleme yöntemleri

PDF metin çıkarımı sonrasında sayfa başlığı temizliği, Unicode NFC normalizasyonu, özel boşluk ve fi/fl birleşik karakter düzeltmeleri ile metin aralığı düzeltmeleri için ayrı betikler kullanılmıştır.

Son korpusta kullanılan temiz metin sürümleri envanterde açıkça kayıtlıdır.

## 3. Kaynak ve çıktı bütünlüğü

- Ham PDF SHA-256: **12/12 PASS**
- Temiz metin SHA-256: **12/12 PASS**
- Son korpus metniyle birebir eşleşme: **12/12 PASS**

| Kanun | Son temiz metin | İlk karakter | Son karakter | Fark (ilk-son) |
|---|---|---:|---:|---:|
| 2709 | `anayasa_spacing_fixed.txt` | 193913 | 193904 | 9 |
| 4721 | `medeni_kanun_spacing_fixed.txt` | 388119 | 388195 | -76 |
| 6098 | `borclar_kanunu_spacing_fixed.txt` | 290462 | 290707 | -245 |
| 5237 | `ceza_kanunu_spacing_fixed.txt` | 281727 | 281873 | -146 |
| 5271 | `ceza_muhakemesi_kanunu_spacing_fixed.txt` | 340853 | 340938 | -85 |
| 4857 | `is_kanunu_spacing_fixed.txt` | 141511 | 141531 | -20 |
| 6102 | `ticaret_kanunu_spacing_fixed.txt` | 964272 | 964784 | -512 |
| 6502 | `tuketici_kanunu_spacing_fixed.txt` | 137928 | 138001 | -73 |
| 2577 | `idari_yargilama_kanunu_spacing_fixed.txt` | 99088 | 99116 | -28 |
| 213 | `vergi_usul_kanunu_spacing_fixed.txt` | 491269 | 491897 | -628 |
| 2004 | `icra_iflas_kanunu_spacing_fixed.txt` | 417566 | 418278 | -712 |
| 5510 | `sosyal_sigortalar_kanunu_sh_fixed.txt` | 722424 | 722055 | 369 |

Bu karakter farkları doğrudan silinen hukuki içerik miktarı olarak yorumlanamaz.

## 4. Chunking yöntemleri

| Yöntem | Train | Validation | Test | Toplam | Olası cümle ortası bölünme | Kelime bölünmesi örneği |
|---|---:|---:|---:|---:|---:|---:|
| original | 881 | 40 | 59 | 980 | 52 | 0 |
| sentence_aware | 884 | 40 | 59 | 983 | 26 | 1 |
| legal_aware | 889 | 40 | 59 | 988 | 32 | 0 |

Üç sürümün tamamında 2.048 token üst sınırı sağlandı. Raporlanan chunk bütünlük hatası bulunmadı.

Son veri seti dokümantasyonunda **legal-aware** sürüm referans alınmıştır. Bu sürümün kullanılmış olması, model eğitimi veya RAG kullanımının gerçekleştiği anlamına gelmez.

## 5. Eleme ve inceleme durumu

Bu aşamada 12 kanunun herhangi birinin korpustan çıkarıldığına ilişkin bulgu yoktur. 980/983/988 farkı, farklı chunking stratejilerinin ürettiği parça sayılarıdır.

**Legal-aware:** 988 chunk'ın tamamında `requires_manual_review=True`.

53 adet büyük birimin parçalanması gerekmiştir. Olası cümle ortası bölünmelerin inceleme gerektirdiği ayrıca not edilmiştir.

## 6. Sınırlılıklar

- Dosya hash kontrolu hukuki dogruluk kaniti degildir.
- Karakter sayisi farki tek basina icerik kaybini kanitlamaz veya dislamaz.
- 988 legal-aware chunk icin manuel inceleme gereklidir.
- Chunking surumleri arasindaki sayi farki silinen kanun veya kayit sayisi degildir.
- Olası cumle ortasi bolunmeler heuristik sinyaldir.
- Kaynak guncelligi ve hukuki icerik bagimsiz olarak dogrulanmamistir.
- Veri kullanim haklari ve model egitim izni bu teknik denetimle verilmez.

## 7. Kaynak hakları ve eğitim onayı

- Kaynak hak durumu dağılımı: `{'incelenecek': 12}`
- Kaynak kalite durumu dağılımı: `{'otomatik_temizlik_yapildi_insan_kontrolu_bekliyor': 12}`
- `training_candidate` dağılımı: `{'True': 902, 'False': 86}`
- `training_approved = false`
- `rights_status = pending_review`

## 8. Kanıt dosyaları

- `reports/quality/domain_cleaning_integrity_v0.9.json`
- `reports/quality/domain_chunk_final_comparison_v0.9.json`
- `reports/statistics/domain_chunk_stats_v0.9.json`
- `reports/statistics/domain_chunk_stats_sentence_aware_v0.9.json`
- `reports/statistics/domain_chunk_stats_legal_aware_v0.9.json`
- `reports/sources/legislation_documents.csv`
- `scripts/10_clean_anayasa.py`
- `scripts/13_remove_page_headers.py`
- `scripts/14_normalize_legislation.py`
- `scripts/15_fix_legislation_spacing.py`
- `scripts/18_build_domain_corpus.py`
- `scripts/29_chunk_domain_corpus.py`
- `scripts/32_chunk_domain_corpus_sentence_aware.py`
- `scripts/34_chunk_domain_corpus_legal_aware.py`

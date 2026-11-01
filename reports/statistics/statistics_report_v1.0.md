# LexiTech TR — İstatistik Raporu v1.0-rc1

Bu dosya `scripts/09_statistics.py` ile üretilir, elle düzenlenmez.

## Sayısal özet

| Özellik | Değer |
|---|---|
| Veri kaynağı sayısı | 3 |
| Ham kanun dokümanı (PDF) | 12 |
| Extraction başarılı / başarısız | 12 / 0 |
| Final kanun dokümanı | 12 |
| Toplam kelime (domain) | 581.694 |
| Toplam token (domain) | 1.595.233 |
| Eğitime giren token (domain) | 1.439.417 |
| Eğitim chunk'ı | 820 |
| Türkçe chunk oranı | %99,9 |
| Ham soru-cevap kaydı | 378.903 |
| Birebir tekrar | 70.893 |
| Yakın tekrar | 112 |
| Kanun metniyle desteklenen aday | 28.866 |
| Final instruction örneği | 4.000 |
| Domain insan kontrol örneği | 0 |
| Instruction insan kontrol örneği | 0 |
| Instruction asistan ön incelemesi | 170 / 200 |

## Verinin aşamalar boyunca erimesi

### Domain Corpus

| Aşama | Birim | Sayı |
|---|---|---|
| Ham PDF | doküman | 12 |
| Extraction sonrası | doküman | 12 |
| Temizleme sonrası | doküman | 12 |
| Chunk üretimi | chunk | 906 |
| Değişiklik tabloları çıkarıldıktan sonra | chunk | 820 |

### Instruction Dataset

| Aşama | Kayıt |
|---|---|
| Ham | 378.903 |
| Temizleme sonrası | 378.902 |
| Birebir tekrar ayıklama sonrası | 308.009 |
| Kanun metni filtresi ve yakın tekrar sonrası | 28.866 |
| Görev dengeli seçim + kanundan üretilen + sınır örnekleri | 4.000 |

## Çıkarma nedenleri (instruction)

| Neden | Kayıt |
|---|---|
| source_artifact | 96.321 |
| unverifiable_case_law | 69.259 |
| no_resolvable_citation | 33.680 |
| low_evidence | 30.147 |
| law_outside_corpus | 24.565 |
| context_dependent | 17.644 |
| too_short | 1.741 |
| draft_legislation | 1.328 |
| numeric_mismatch | 1.318 |
| alternative_answer | 969 |
| article_not_found | 914 |
| too_long | 581 |
| repealed_article | 384 |
| truncated_answer | 180 |
| near_duplicate | 112 |

## Görev türü dağılımı

| Görev türü | Ne yapar | Örnek | Oran |
|---|---|---|---|
| Usul ve süre | Başvuru yolu, süre ve görevli mahkemeyi söyler | 798 | %19,9 |
| Koşul ve unsur | Bir kurumun şartlarını veya suçun unsurlarını sıralar | 794 | %19,9 |
| Tanım ve açıklama | Bir kavramı açıklar | 650 | %16,2 |
| Madde bulma | Konunun hangi kanun maddesinde olduğunu gösterir | 351 | %8,8 |
| Hukuki sonuç | Bir durumun doğurduğu sonucu açıklar | 335 | %8,4 |
| Karşılaştırma | İki kurumu karşılaştırır | 275 | %6,9 |
| Bilgi yetersizliği | Doğrulanamayan soruda sınırını bildirir | 229 | %5,7 |
| Olaya uygulama | Hükmü verilen olaya uygular | 207 | %5,2 |
| Yaptırım | Öngörülen cezayı veya yaptırımı söyler | 189 | %4,7 |
| Neden-sonuç | Bir kuralın amacını veya nedenini açıklar | 90 | %2,2 |
| Alan dışı | Hukuk dışı soruyu reddeder | 42 | %1,1 |
| Madde açıklama | Bir maddenin içeriğini açıklar | 40 | %1,0 |

## Instruction split

| Küme | Örnek |
|---|---|
| test | 216 |
| train | 3.568 |
| validation | 216 |

## Kanun dağılımı (instruction, ilk atıf)

| Kanun | Örnek |
|---|---|
| 5237 | 684 |
| 5271 | 472 |
| 6098 | 470 |
| 4721 | 455 |
| 2004 | 305 |
| 4857 | 261 |
| 5510 | 260 |
| 6102 | 211 |
| 6502 | 197 |
| 2577 | 193 |
| 213 | 127 |
| 2709 | 94 |

## Alt konu dağılımı (domain, eğitim tokenı)

| Alt konu | Token | Oran |
|---|---|---|
| ticaret_hukuku | 323.273 | %22,5 |
| sosyal_guvenlik_hukuku | 221.565 | %15,4 |
| vergi_hukuku | 155.098 | %10,8 |
| icra_iflas_hukuku | 139.858 | %9,7 |
| medeni_hukuk | 130.897 | %9,1 |
| ceza_muhakemesi | 108.444 | %7,5 |
| borclar_hukuku | 99.191 | %6,9 |
| ceza_hukuku | 87.472 | %6,1 |
| anayasa_hukuku | 57.411 | %4,0 |
| is_hukuku | 43.678 | %3,0 |
| tuketici_hukuku | 42.458 | %2,9 |
| idare_hukuku | 30.072 | %2,1 |

En büyük doküman Türk Ticaret Kanunu: toplam tokenın %21,0 kadarı.

## Token dağılımı

| Ölçüt | Adet | Toplam | Min | Medyan | Ortalama | P95 | Maks |
|---|---|---|---|---|---|---|---|
| Kanun dokümanı | 12 | 1.595.233 | 36421 | 113291.5 | 132936.1 | 334956 | 334956 |
| Eğitim chunk'ı | 820 | 1.439.417 | 59 | 1902.5 | 1755.4 | 2037 | 2048 |
| Instruction soru | 4.000 | 158.580 | 8 | 35.0 | 39.6 | 79 | 167 |
| Instruction cevap | 4.000 | 450.232 | 21 | 95.0 | 112.6 | 263 | 849 |

Tokenizer: `Qwen/Qwen2.5-3B-Instruct`.

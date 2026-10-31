# LexiTech TR — İstatistik Raporu v1.0-rc1

Bu dosya `scripts/09_statistics.py` ile üretilir, elle düzenlenmez.

## Sayısal özet

| Özellik | Değer |
|---|---|
| Veri kaynağı sayısı | 3 |
| Ham kanun dokümanı (PDF) | 12 |
| Extraction başarılı / başarısız | 12 / 0 |
| Final kanun dokümanı | 12 |
| Toplam kelime (domain) | 582.750 |
| Toplam token (domain) | 1.595.752 |
| Eğitime giren token (domain) | 1.439.916 |
| Eğitim chunk'ı | 820 |
| Türkçe chunk oranı | %99,9 |
| Ham soru-cevap kaydı | 378.903 |
| Birebir tekrar | 70.893 |
| Kanun metniyle desteklenen aday | 31.962 |
| Final instruction örneği | 4.000 |

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
| Kanun metni filtresi ve yakın tekrar sonrası | 31.962 |
| Görev dengeli seçim + kanundan üretilen + sınır örnekleri | 4.000 |

## Çıkarma nedenleri (instruction)

| Neden | Kayıt |
|---|---|
| unverifiable_case_law | 78.837 |
| source_artifact | 62.102 |
| no_resolvable_citation | 40.016 |
| low_evidence | 36.524 |
| law_outside_corpus | 27.590 |
| context_dependent | 23.056 |
| too_short | 1.741 |
| draft_legislation | 1.477 |
| numeric_mismatch | 1.175 |
| alternative_answer | 1.091 |
| article_not_found | 1.044 |
| too_long | 581 |
| repealed_article | 512 |
| truncated_answer | 180 |
| near_duplicate | 121 |

## Görev türü dağılımı

| Görev türü | Ne yapar | Örnek | Oran |
|---|---|---|---|
| Usul ve süre | Başvuru yolu, süre ve görevli mahkemeyi söyler | 800 | %20,0 |
| Koşul ve unsur | Bir kurumun şartlarını veya suçun unsurlarını sıralar | 797 | %19,9 |
| Tanım ve açıklama | Bir kavramı açıklar | 622 | %15,6 |
| Madde bulma | Konunun hangi kanun maddesinde olduğunu gösterir | 351 | %8,8 |
| Hukuki sonuç | Bir durumun doğurduğu sonucu açıklar | 338 | %8,4 |
| Karşılaştırma | İki kurumu karşılaştırır | 278 | %7,0 |
| Bilgi yetersizliği | Doğrulanamayan soruda sınırını bildirir | 229 | %5,7 |
| Olaya uygulama | Hükmü verilen olaya uygular | 219 | %5,5 |
| Yaptırım | Öngörülen cezayı veya yaptırımı söyler | 194 | %4,8 |
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
| 5237 | 627 |
| 5271 | 459 |
| 6098 | 459 |
| 4721 | 445 |
| 2004 | 309 |
| 4857 | 283 |
| 5510 | 260 |
| 6102 | 236 |
| 6502 | 209 |
| 2577 | 201 |
| 213 | 142 |
| 2709 | 99 |

## Alt konu dağılımı (domain, eğitim tokenı)

| Alt konu | Token | Oran |
|---|---|---|
| ticaret_hukuku | 323.355 | %22,5 |
| sosyal_guvenlik_hukuku | 221.658 | %15,4 |
| vergi_hukuku | 155.121 | %10,8 |
| icra_iflas_hukuku | 139.906 | %9,7 |
| medeni_hukuk | 130.988 | %9,1 |
| ceza_muhakemesi | 108.475 | %7,5 |
| borclar_hukuku | 99.241 | %6,9 |
| ceza_hukuku | 87.488 | %6,1 |
| anayasa_hukuku | 57.414 | %4,0 |
| is_hukuku | 43.702 | %3,0 |
| tuketici_hukuku | 42.461 | %2,9 |
| idare_hukuku | 30.107 | %2,1 |

En büyük doküman Türk Ticaret Kanunu: toplam tokenın %21,0 kadarı.

## Token dağılımı

| Ölçüt | Adet | Toplam | Min | Medyan | Ortalama | P95 | Maks |
|---|---|---|---|---|---|---|---|
| Kanun dokümanı | 12 | 1.595.752 | 36456 | 113315.0 | 132979.3 | 335040 | 335040 |
| Eğitim chunk'ı | 820 | 1.439.916 | 59 | 1902.5 | 1756.0 | 2038 | 2048 |
| Instruction soru | 4.000 | 159.170 | 8 | 35.0 | 39.8 | 79 | 155 |
| Instruction cevap | 4.000 | 458.725 | 21 | 97.0 | 114.7 | 267 | 937 |

Tokenizer: `Qwen/Qwen2.5-3B-Instruct`.

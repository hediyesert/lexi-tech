# LexiTech TR Domain Corpus v1.0-rc1

**Durum:** Teknik olarak eğitime hazır aday. İnsan kalite kontrolü yapılmadı, kullanım hakkı onayı bekliyor,
`training_approved=false`.

## Amaç

Türk hukuku alanında soru cevaplayabilen bir dil modelinin continued pretraining (CPT) aşamasında kullanılmak
üzere hazırlandı. Genel amaçlı bir Türkçe corpus değildir. Vize aşamasında model eğitimi yapılmadı.

## Kapsam

Kapsam içi: 12 temel kanunun yürürlükteki birleştirilmiş metni.
Kapsam dışı: yargı kararları, yönetmelik ve tebliğler, doktrin, 12 kanun dışındaki mevzuat. Ayrıntı:
[reports/problem_definition.md](reports/problem_definition.md).

## Veri kaynakları

| Kaynak | Tür | Dil | Doküman | Lisans / kullanım |
|---|---|---|---:|---|
| Mevzuat Bilgi Sistemi | PDF | tr | 12 | Resmî metin, kullanım koşulu incelenecek |

Hukuk metninde en güvenilir kaynak resmî yayın olduğu için tek kaynak bilinçli seçildi. Kaynak bağımlılığı
yazım biçimi açısından yüksektir; bu bir sınırlılıktır. Tam liste:
[reports/sources/data_sources.csv](reports/sources/data_sources.csv).

## Veri toplama

Kanunlar 19-20 Ekim 2026'da mevzuat.gov.tr sayfalarından tarayıcıyla PDF olarak kaydedildi, bu yüzden indirme
adımı script değildir. Dosyalar `data/raw/legislation/` altında değiştirilmeden saklanır, her çalışmada
SHA-256 ile doğrulanır. Belgeye özel URL'ler PDF altbilgisinden okundu, adreslerin canlı erişimi bu ortamda
denenemedi.

## İşleme adımları

- **Extraction:** pypdf. 1.540 sayfa, 12 dokümanın 12'si başarılı. Taranmış sayfa yok, OCR gerekmedi.
- **Cleaning:** Sayfa başlığı silme, NFC, kırık kelime ve harf aralığı onarımı (2.266 kelime), boşluk ve satır
  normalizasyonu. Boşluk dışı karakterin değişmediği hash ile doğrulanır. Kurallar:
  [reports/cleaning_rules.md](reports/cleaning_rules.md).
- **Filtering:** Hiçbir kanun elenmedi. 86 değişiklik tablosu chunk'ı kanun hükmü olmadığı için eğitimden çıkarıldı.
- **Deduplication:** Dokümanlar farklı kanunlar olduğu için doküman düzeyinde tekrar yok; chunk düzeyinde
  birebir tekrar testi temiz.

## Format

JSONL. `domain_corpus_v1.0.jsonl` doküman düzeyindedir: `document_id`, `title`, `source`, `url`, `language`,
`document_type`, `publication_year`, `subtopic`, `char_count`, `token_count`, `text` ve ek olarak `law_number`,
`version_date`, `raw_sha256`, `text_sha256`, `sections`.

`train.jsonl`, `validation.jsonl`, `test.jsonl` chunk düzeyindedir ve CPT için kullanılır.

## İstatistikler

| Ölçüt | Değer |
|---|---:|
| Doküman | 12 |
| Toplam kelime | 581.694 |
| Toplam token | 1.595.233 |
| Eğitime giren token | 1.439.417 |
| Eğitim chunk'ı | 820 |
| Medyan chunk | 1.902 token |
| Türkçe chunk | %99,9 (820 chunk'ın 1'i otomatik tespitte farklı dil) |

Dağılım ve alt konular: [reports/statistics/statistics_report_v1.0.md](reports/statistics/statistics_report_v1.0.md).

## Veri ayrımı

Doküman düzeyinde: 10 kanun train, Anayasa validation, Türk Ceza Kanunu test. Chunk'lar split'ten sonra üretildi,
bu yüzden aynı kanunun parçaları iki kümeye düşmez. Küme başına chunk: 738 / 33 / 49. Token oranı yaklaşık
%90 / %4 / %6.

Parçalama madde sınırlarını ve üst sınır olarak 2.048 token gözetir. Madde başlığı kendi maddesiyle kalır.

## Lisans ve kullanım

Kullanım hakları incelemesi tamamlanmadı, `rights_status=pending_review`. Kanun metinlerinin kullanım serbestisi
danışmanla netleştirilmeli. Kişisel veri beklenmez, mevzuat metnidir.

## Bilinen problemler

- 1,44 milyon eğitim tokenı CPT için küçüktür. Model alan dilini sınırlı ölçüde öğrenir.
- Metne yapışık dipnot rakamları var (`Belirlenmesi2`), karakter değiştirmemek için silinmedi.
- Tablolarda sütun yapısı kaybolmuştur.
- Az sayıda kırık kelime kalmıştır (`Pa şa`, `bro şür`).
- Test yalnızca ceza hukuku, validation yalnızca anayasa hukukudur. Küme sonuçları genellenemez.
- Bazı bölüm başlıkları önceki chunk'ın sonunda kalır.
- Metinler Ekim 2026 tarihlidir, güncellik zamanla bozulur.

## Sınırlılıklar

Bu veri seti hukuki danışmanlık aracı değildir. Yalnızca kanun metni içerir, yargı kararı içermez. Yürürlük
tarihine bağlı geçiş hükümleri ayrıca yorum gerektirir.

## Sürüm geçmişi

- v0.9 (27.10.2026): Extraction, temizleme, token sayımı, üç chunk denemesi.
- v1.0-rc1 (31.10.2026): Tek pipeline, tüm kanunlarda kırık kelime onarımı, tam metadata, tek chunk sürümü.

## Hazırlayanlar

[ad soyad], [ad soyad], [ad soyad]. Danışman: [ad soyad].

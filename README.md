# LexiTech TR

Türk hukuku için yapay zekâ destekli hukuk asistanı projesi. Hedef kullanıcılar stajyer avukatlar, hukuk
öğrencileri, avukatlar ve hukuki bilgiye erişmek isteyen vatandaşlardır.

**Durum: v1.0-rc1.** Veri setleri teknik olarak hazır. İnsan kalite kontrolü ve kullanım hakkı onayı tamamlanmadı.
Vize aşamasında model eğitimi yapılmadı. Bu proje hukuki danışmanlık sunmaz.

## Hedef ve mevcut durum

| Hedef | Mevcut durum |
|---|---|
| Türk hukuku sorularını cevaplamak | Veri hazır, model henüz yok |
| Kanun ve madde bulmak | 12 kanun, 351 madde bulma örneği |
| Yargı kararıyla desteklenen analiz | Yok. Corpus'ta karar metni bulunmuyor, karar atıflı kayıtlar elendi |
| Dilekçe taslağı | Yok |
| Doğrulanabilir kaynağa dayanmak | Her kaynaklı örnek kanun maddesine bağlı; hukuki doğruluk insanla doğrulanmadı |
| Uydurma madde ve karar riskini azaltmak | 229 bilgi yetersizliği örneği; etkisi model eğitilmeden ölçülemez |
| Türk hukukunun geniş alanı | 12 temel kanun. Geniş kapsam uzun vadeli hedef |

## Veri setleri

| | Domain Corpus | Instruction Dataset |
|---|---|---|
| Kullanım | CPT | SFT |
| Boyut | 12 kanun, 820 chunk, 1,44M eğitim tokenı | 4.000 örnek |
| Split | 738 / 33 / 49 chunk | 3.568 / 216 / 216 örnek |
| Kart | [DATASET_CARD.md](DATASET_CARD.md) | [INSTRUCTION_CARD.md](INSTRUCTION_CARD.md) |

## Kurulum ve çalıştırma

```bash
python3.11 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python scripts/run_pipeline.py
```

İlk adımı atlamak için:

```bash
.venv/bin/python scripts/run_pipeline.py --from-step 02_extract.py
```

Otomatik kalite testleri:

```bash
.venv/bin/python -m pytest tests -q
```

Kanun PDF'leri otomatik indirilmez, tarayıcıyla kaydedildi. Pipeline'ı sıfırdan çalıştırmak için `data/raw/legislation/`
gerekir. Tüm yollar ve eşikler `config.yaml` içindedir, rastgelelik `random_seed: 42` ile sabitlenmiştir.

## Pipeline

| Adım | Script | Çıktı |
|---|---|---|
| İndirme | `01_download.py` | `data/raw/` |
| Extraction | `02_extract.py`, `02b_extract_legislation.py` | `data/extracted/` |
| Temizleme | `03_clean.py`, `03b_clean_legislation.py` | `data/cleaned/` |
| Birebir tekrar | `04_deduplicate_exact.py` | `data/deduplicated/` |
| Domain Corpus | `05_build_domain_corpus.py` | `data/final/` |
| Filtre ve yakın tekrar | `06_filter_instruction.py` | `data/interim/` |
| Instruction seti | `07_build_instruction_set.py` | `data/final/instruction_v1.0/` |
| Token sayımı | `08_token_count.py` | `reports/statistics/` |
| İstatistik | `09_statistics.py` | `reports/statistics/` |
| Kalite örneklemi | `10_sample_quality_review.py` | `reports/quality/` |
| Kalite raporu | `11_quality_report.py` | `reports/quality/` |

## Veri nerede

`data/` Git'e girmez, boyutu 1,6 GB'tır. Kaynak dosyalar Hugging Face'ten ve mevzuat.gov.tr'den alınır; bütünlük
değerleri `reports/manifests/` ve `reports/sources/legislation_documents.csv` içindedir. Üretilen dosyalar yerel
ortamda tutulur. Paylaşım yeri: [belirlenecek].

## Belgeler

- [Vize uyum raporu](reports/VIZE_UYUM_RAPORU.md): rehberle karşılaştırma ve 19 sorunun cevabı
- [Problem tanımı](reports/problem_definition.md)
- [Kaynak listesi](reports/sources/data_sources.csv)
- [Temizleme kuralları](reports/cleaning_rules.md) ve [öncesi-sonrası örnekleri](reports/cleaning_examples_v1.0.md)
- [İstatistik raporu](reports/statistics/statistics_report_v1.0.md)
- [Kalite kontrol raporu](reports/quality/quality_control_report_v1.0.md)
- [Değerlendirme planı](reports/evaluation_plan.md)
- [Literatür taraması (taslak)](reports/literature_review.md)
- [Danışman soruları (taslak)](reports/advisor_questions.md)
- [İnsan kalite kontrolü dosyası](reports/quality/kalite_inceleme_v1.0.xlsx): doldurduktan sonra `python scripts/qc_review_sheet.py import`
- [Deney günlüğü](experiments.md)
- [v0.9 arşivi](archive/README.md)

## Bilinen sınırlılıklar

- Kullanım hakları onaylanmadı. Instruction kaynaklarının büyük kısmının lisansı belirsizdir.
- Örnekler otomatik doğrulandı, hukukçu onayı yoktur.
- Domain Corpus küçüktür ve yalnızca kanun metni içerir.

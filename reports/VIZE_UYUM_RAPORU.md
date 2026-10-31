# LexiTech TR — Vize Rehberi Uyum Raporu

**Tarih:** 31.10.2026. **Sürüm:** v1.0-rc1.

## Sonuç

Teslim edilecek 9 kalemin 6'sı hazır. Sunum taslak olarak hazır, ad ve danışman bilgisi eksik. Kalite kontrol
raporu hazır ancak insan incelemesi yapılmadı. Git deposunda uzak depo tanımlı değil. Bu işler ile kullanım hakkı
kararı grup üyelerini bekliyor.

## Teslim kalemleri

| # | Kalem | Durum | Dosya |
|---:|---|---|---|
| 1 | Veri kaynakları listesi | Hazır | `reports/sources/data_sources.csv` |
| 2 | Domain Corpus | Aday hazır | `data/final/domain_corpus_v1.0.jsonl`, `train/validation/test.jsonl` |
| 3 | Instruction Dataset | Aday hazır | `data/final/instruction_v1.0.jsonl`, `instruction_v1.0/` |
| 4 | Preprocessing kodları | Hazır | `scripts/`, `tests/` |
| 5 | Dataset Card | Hazır, isimler eksik | `DATASET_CARD.md`, `INSTRUCTION_CARD.md` |
| 6 | İstatistik raporu | Hazır | `reports/statistics/statistics_report_v1.0.md` |
| 7 | Kalite kontrol raporu | Kısmen. 200 örneklik asistan incelemesi var, insan incelemesi yok | `reports/quality/quality_control_report_v1.0.md` |
| 8 | Git deposu | Commit edildi, uzak depo tanımlı değil | `vize-v1.0-rc1` branch'i |
| 9 | Sunum | Taslak hazır, isimler eksik | [LexiTech TR Vize Sunumu](https://claude.ai/artifact/Q5pfnhG4dCVUjLAvrfLaxx) |

## Rehber bölümleri

| Bölüm | Önceki durum | Şimdi |
|---|---|---|
| 3. Problem tanımı | Yazılı kapsam yoktu | `reports/problem_definition.md` |
| 4. Kaynaklar | Tablo eksikti, URL'ler 12/12 boştu | Rehber biçiminde tablo, 12/12 belge URL'si |
| 5. Ham veri | Uygun | Değişmedi |
| 6. Extraction | Script yoktu, başarı oranı ölçülmemişti | `02b_extract_legislation.py`, %100 başarı, 1.540 sayfa |
| 7. Temizleme | 8 script, argümanlar kayıtsız, boşluklar temizlenmemişti | Tek script, kural listesi, 24 öncesi-sonrası örneği |
| 8. Tekrar | Soru bazlı yakın tekrar taraması yoktu | Tüm adaylarda soru bazlı MinHash, kümeler arası test |
| 9. Metadata | `publication_year`, `subtopic`, URL yoktu | Rehber alanlarının tamamı |
| 10. Token, split | Instruction token yoktu, config %80/10/10 yazıyordu | Tam dağılım, config gerçek oranla uyumlu |
| 11. Instruction | 124.510 kayıt, `other` %49, sınır örneği yok | 4.000 örnek, 12 görev türü, 271 sınır örneği |
| 12. Kalite | 200 kaydın 2'si bakılmıştı | Otomatik testler, asistan turu, insan örneklemi hazır |
| 13. Yeniden üretim | Tek komut yoktu, 95 script | `run_pipeline.py`, 13 adım, log, sabit seed |
| 14-16. Plan ve sunum | Sunum yoktu | Taslak hazır |

## Temizlenen fazlalıklar

Hiçbir şey silinmedi, her şey `archive/` altına taşındı.

- 91 script: tek seferlik kayıt script'leri, eski sınıflandırıcı sürümleri, denemeler.
- 953 MB veri: üç ayrı instruction kopyası, üç chunk sürümü, `*_before_*` yedekleri, eski `spacing_fixed` katmanları.
- v0.9 raporları ve boş `.backup` dosyaları.

## Kaynak veriye ilişkin ana karar

Rehber "on bin otomatik örnek yerine kontrol edilmiş üç bin örnek" der. Bu yüzden 124.510 kayıt düzeltilmedi,
kanun metniyle desteklenen kayıtlardan 4.000'lik yeni set seçildi. v0.9 kartlarındaki "henüz v1.0 değil" ilkesi
korundu: dosyalar v1.0 adını taşır, durum `1.0-rc1` kalır, `training_approved=false` değişmez.

## Teslimden önce kendinize sorun

| # | Soru | Cevap |
|---:|---|---|
| 1 | Hangi alanda uzmanlaşacak? | Türk hukuku. Mevcut kapsam 12 temel kanun |
| 2 | Veriler nereden, neden? | mevzuat.gov.tr resmî metin olduğu için; iki Hugging Face veri seti soru-cevap havuzu için |
| 3 | Kullanma hakkımız var mı? | **Henüz belirsiz.** Onay yok; danışman kararı gerekli |
| 4 | Kaç ham doküman, kaçı işlendi? | 12 PDF'in 12'si; 378.903 soru-cevabın 4.000'i finalde |
| 5 | Metni nasıl çıkardık, temizledik? | pypdf; `reports/cleaning_rules.md` |
| 6 | Hangi verileri neden çıkardık? | Neden tablosu istatistik raporunda, her kayıt loglu |
| 7 | Exact ve near duplicate? | SHA-256; soru metninde MinHash + Jaccard ≥ 0,85 |
| 8 | Metadata? | `DATASET_CARD.md` ve `INSTRUCTION_CARD.md` Format bölümleri |
| 9 | Kaç token, hangi alt konular? | 1.595.233 token, 12 hukuk alanı |
| 10 | Dil dağılımı? | Domain %99,9 Türkçe; instruction cevaplarının tamamı Türkçe (otomatik tespit) |
| 11 | Split ve leakage? | Domain doküman düzeyinde; instruction kaynak dosya ve madde düzeyinde ayrık, testle doğrulanıyor |
| 12 | Manuel kalite kontrol? | **Eksik.** Asistan turu yapıldı, insan incelemesi bekliyor |
| 13 | Corpus ve instruction farkı? | Corpus alanı öğretir (CPT), instruction görevi öğretir (SFT) |
| 14 | Örnekler nasıl oluştu, doğrulandı mı? | LLM ile üretilmiş kaynak havuzu, kanun metnine karşı otomatik filtre |
| 15 | Görev türleri? | 12 tür, en büyüğü %20; `INSTRUCTION_CARD.md` |
| 16 | Aynı dokümandan örnekler ayrı kümede mi? | Hayır, `tests/test_release.py` doğruluyor |
| 17 | Yeniden çalıştırılabilir mi? | Evet, `run_pipeline.py`. Aynı girdiyle aynı dosya hash'leri üretildiği doğrulandı |
| 18 | Bilinen eksikler? | Kartların Bilinen Problemler bölümleri |
| 19 | Eğitimde kullanılabilir mi? | Teknik olarak evet. Hak ve insan kontrolü tamamlanmadan onay verilemez |

## Grubun yapması gerekenler

1. **İnsan kalite kontrolü.** `reports/quality/kalite_inceleme_v1.0.xlsx` dosyasında 200 instruction ve 150 domain
   örneği, kaynak metniyle yan yana duruyor. Sarı sütunları doldurun, sonra
   `python scripts/qc_review_sheet.py import` ve `python scripts/11_quality_report.py` çalıştırın.
   Asistan görüşleri ayrı sütunlarda, şüpheli satırlar üstte. İnsan onayı yerine geçmez.
2. **Kullanım hakkı.** `reports/advisor_questions.md` taslağını kendi adınızla danışmana gönderin.
3. **Hukukçu görüşü.** En azından test kümesi örneklenmeli.
4. **Literatür.** `reports/literature_review.md` taslak. Birincil kaynakları okuyup sayıları doğrulayın.
5. **Sunum ve kartlar.** Grup ve danışman adlarını ekleyin, kalite slaydına insan sonuçlarını yazın.
6. **Veri paylaşımı.** README'de büyük dosyaların yerini yazın.
7. **Uzak depo.** Değişiklikler `vize-v1.0-rc1` branch'inde. Depoda remote tanımlı değil, teslim için bir uzak depoya
   gönderilmesi gerekir.

## Hedeften uzak kalan alanlar

Bunlar vizede zorunlu değil, ancak proje hedefiyle arasındaki farkı gösterir.

- **Yargı kararı yok.** 69.259 kayıt karar atfı nedeniyle elendi. Hedef için resmî karar kaynağından corpus gerekir.
- **Corpus küçük.** 1,44M token, rehberin örnek ölçeğinin (65M) çok altında. Daha çok kanun ve karar metni eklenmeli.
- **Tek kaynak bağımlılığı.** Kaynaklı örneklerin %98'i lisansı belirsiz tek veri setinden geliyor.
- **Dilekçe ve özetleme görevi yok.**

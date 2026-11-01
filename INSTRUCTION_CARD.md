# LexiTech TR Instruction Dataset v1.0-rc1

**Durum:** Teknik olarak eğitime hazır aday. İnsan kalite kontrolü yapılmadı, kullanım hakkı onayı bekliyor.
Tüm kayıtlarda `verified=false`, `training_approved=false`.

## Amaç

Modele Türk hukuku sorularını cevaplamayı, ilgili kanun maddesini göstermeyi ve bilmediğini söylemeyi öğretmek
için supervised fine-tuning (SFT) aşamasında kullanılmak üzere hazırlandı.

## Örnek sayısı neden 4.000

Rehberin 3-5 bin hedefine uyar. v0.9'daki 124.510 kayıt kontrol edilemeyecek kadar büyüktü, %49'u görev türüne
ayrılamıyordu. Otomatik üretilmiş büyük bir havuz yerine, kaynağa bağlanmış ve dengeli küçük bir set seçildi.

## Kaynaklar ve üretim yöntemi

| Yöntem | Örnek | Açıklama |
|---|---:|---|
| `llm_uretimi_kaynak_veri_seti` | 3.316 | `sinanelms/hukukisorular`. Yayıncıya göre Gemini 2.5 Pro ile üretildi; prompt ve parametreler bilinmiyor |
| `kaynak_veri_seti_yontem_bilinmiyor` | 62 | `OrionCAF/turkish_law_qa_dataset`. Üretim yöntemi belirsiz |
| `kural_tabanli_kanun_metninden` | 459 | Kanun metninden kuralla üretildi, LLM kullanılmadı |
| `elle_yazilan_sablon` | 163 | Sınır davranışı için elle yazılmış şablonlar |

Proje kapsamında LLM ile yeni örnek üretilmedi. Kural tabanlı ve şablon örnekleri `scripts/07_build_instruction_set.py`
içindedir.

## Görev türü dağılımı

| Görev türü | Örnek | Oran |
|---|---:|---:|
| Usul ve süre | 798 | %20,0 |
| Koşul ve unsur | 794 | %19,9 |
| Tanım ve açıklama | 650 | %16,3 |
| Madde bulma | 351 | %8,8 |
| Hukuki sonuç | 335 | %8,4 |
| Karşılaştırma | 275 | %6,9 |
| Bilgi yetersizliği | 229 | %5,7 |
| Olaya uygulama | 207 | %5,2 |
| Yaptırım | 189 | %4,7 |
| Neden-sonuç | 90 | %2,3 |
| Alan dışı | 42 | %1,1 |
| Madde açıklama | 40 | %1,0 |

Görev türü başına tavan %20, kanun başına tavan %20. Görev türü kural tabanlıdır, ilk kalite turunda 60 kayıtta
54 uyum görüldü. Özetleme ve dilekçe görevi yoktur.

## Doğrulama yöntemi

Her kaynak kaydı `scripts/06_filter_instruction.py` ile kanun metnine bağlanır:

1. Soru ve cevaptaki kanun-madde atıfları çözülür.
2. Madde kanunda yoksa, mülgaysa veya 12 kanun dışındaysa kayıt elenir.
3. Yargı kararı atfı olan kayıt elenir, çünkü corpus'ta karar metni yok.
4. Cevap kelimelerinin maddede geçme oranı ölçülür (kanıt skoru, eşik 0,55).
5. Cevaptaki süreler ve ceza aralıkları maddede veya soruda yoksa kayıt elenir.
6. Kaynak izi taşıyan kayıtlar (site adresi, `(Kaynak: dosya.html)`) elenir.

Bu otomatik kontroldür. **Bir cevabın hukuken doğru olduğunu kanıtlamaz.** Skor kelime örtüşmesidir.

## Elenen kayıtlar

| Aşama | Kayıt |
|---|---:|
| Ham | 378.903 |
| Temizleme sonrası | 378.902 |
| Birebir tekrar sonrası | 308.009 |
| Kanun metni filtresi sonrası | 28.866 |
| Görev türü bilinen ve kümeler arası çakışmayan havuz | 9.803 |
| Final (kaynaklı 3.378 + üretilen 622) | 4.000 |

Neden bazında tablo: [reports/statistics/statistics_report_v1.0.md](reports/statistics/statistics_report_v1.0.md).
Her eleme `data/interim/instruction_exclusions_v1.0.jsonl` dosyasındadır.

## Format

`data/final/instruction_v1.0.jsonl` tamamı, `data/final/instruction_v1.0/` küme dosyalarıdır. Alanlar:

`id`, `split`, `task_type`, `messages`, `instruction`, `response`, `source_document`, `source_articles`,
`generation_method`, `origin`, `evidence_score`, `language`, `verified`, `verified_by`, `rights_status`,
`training_approved`, `dataset_version`.

`source_document` kanun belgesine, `source_articles` maddeye (`5237:81`), `origin` özgün kaynak kayda işaret eder.

## Veri ayrımı

| Küme | Örnek |
|---|---:|
| Train | 3.568 |
| Validation | 216 |
| Test | 216 |

Kümeler arasında ortak kaynak dosyası, ortak kanun maddesi ve soru Jaccard ≥ 0,85 yakın tekrarı yoktur. Test kümesi
böylece modelin eğitimde görmediği maddeleri ölçer. Bu koşullar `tests/test_release.py` ile her çalışmada denenir.
Elle yazılan şablonlarda aile (`family`) bazında ayrım yapıldı.

## Bilinen problemler

- Kaynaklı örneklerin %98'i tek veri setinden gelir, bu setin lisansı belirsizdir.
- Corpus'un ve örneklerin kanun dışına çıkmaması için yorum ağırlıklı cevaplar elendi; cevaplar kanun diline yakındır.
- Şablon örnekleri tekrarlı kalıplar içerir.
- Kişisel veri taraması kural tabanlıdır (e-posta, telefon, IBAN, TCKN); isim tespiti yapılmaz.
- Görev türü etiketleri kural tabanlıdır, bağımsız insan doğrulaması yoktur.
- Aynı konunun farklı sözcüklerle yazılmış soruları kalmıştır (örneğin `mahsup` soruları).
- Asistan incelemesinde kanun metniyle çelişen kayıtlar bulundu, kalıntı hata olasılığı vardır. Hata oranı insan incelemesiyle ölçülmelidir.
- Kanunun Ekim 2026 sürümüyle karşılaştırılır; önceki sürüme göre üretilmiş ve uyuşan cevaplar güncel kabul edilir.

## Lisans ve kullanım

`rights_status=pending_review`. Yayıncı beyanı üst kaynakların haklarını kanıtlamaz. Ayrıntı:
`reports/sources/source_rights_audit_v0.9.csv`, `reports/sources/hf_license_evidence_v0.9.csv`.

## Sürüm geçmişi

- v0.9 (27.10.2026): 124.510 kayıtlık teknik ön taslak.
- v1.0-rc1 (31.10.2026): Kanun metnine bağlı 4.000 örnek, görev dengesi, sınır davranışı örnekleri.

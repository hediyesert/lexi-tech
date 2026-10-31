# LexiTech TR — Kalite Kontrol Raporu v1.0-rc1

Bu dosya `scripts/11_quality_report.py` ile üretilir.

## İnceleme durumu

| İnceleme | Örnek | Durum |
|---|---|---|
| Domain, asistan ön incelemesi | 150 | Tamamlandı. Yalnızca chunk başı ve sonu görüldü |
| Domain, insan incelemesi | 150 | 0 tamamlandı |
| Instruction, asistan ön incelemesi | 60 | Tamamlandı. Kaynaklı kayıtlar, ilk 230 karakter |
| Instruction, insan incelemesi | 200 | 0 tamamlandı |

**Asistan ön incelemesi insan veya hukukçu onayı değildir.** Bu yüzden tüm kayıtlarda `verified=false` ve `training_approved=false` kalır.

## Domain Corpus: ilk tur sonuçları

Asistan turu temizleme düzeltilmeden önceki 150 chunk üzerindedir (`qc_domain_assistant_round1_v1.0.csv`). İnsan incelemesi güncel veriden çekilen ayrı 150 chunk içindir.

| Kontrol | Asistan | İnsan |
|---|---|---|
| Okunabilir metin | 142/150 (%94,7) | yapılmadı |
| Doğru domain | 150/150 (%100,0) | yapılmadı |
| Extraction doğru | 148/150 (%98,7) | yapılmadı |
| Header/footer temiz | 147/150 (%98,0) | yapılmadı |
| Bozuk karakter yok | 150/150 (%100,0) | yapılmadı |
| Metadata doğru | 150/150 (%100,0) | yapılmadı |

### Bulunan hata türleri ve yapılan düzeltme

| Hata | Sonuç |
|---|---|
| Harf aralıklı metin, kopuk baş harf (`B u K a n u n`, `Y aşlılığı`) | Düzeltildi: `join_fragments`, `collapse_letter_spacing` |
| Kısmi harf aralığı (`p a r ç a l a r a`, `olunmamı şsa`) | Düzeltildi: `join_impossible_onset` ve genişletilmiş `collapse_letter_spacing` |
| Boşluklu işaret (`( 1 )`, `IV .`) | Düzeltildi: `normalize_whitespace` |
| Metne yapışık dipnot rakamı (`Belirlenmesi2`) | Düzeltilmedi. Rakam silmek karakter değiştirmektir; bilinen sorun |
| Tablo yapısının kaybı | Düzeltilmedi; bilinen sorun |

## Instruction Dataset: ilk tur sonuçları

Rastgele 200 örneklemdeki kaynaklı kayıtlardan 60 tanesi madde metniyle karşılaştırıldı.

| Sonuç | Kayıt |
|---|---|
| consistent_with_excerpt | 56 |
| reject | 3 |
| needs_legal_review | 1 |

Görev türü uyumu: 54/60.

### Hatadan türetilen kurallar

| Bulgu | Eklenen kural | Elenen kayıt |
|---|---|---|
| Cevapta site adresi | `source_artifact` | 96321 |
| Soruda karar numarası (YCGK) | `unverifiable_case_law` genişletildi | sayıma dahil |
| LLM notu (`metindeki`, `sehven`) | `context_dependent` genişletildi | sayıma dahil |
| `nedeni`, `sebebi` görev türünü yanıltıyor | `neden_sonuc` kuralı daraltıldı | yeniden sınıflandırıldı |

## Instruction Dataset: ikinci tur sonuçları

200 rastgele örneğin 170'i okundu. Kısa maddelerde tam metin, uzun maddelerde cevaba en yakın satırlar karşılaştırıldı, 750 karakteri aşan cevapların sonu her zaman görülmedi. Kural ve şablon örnekleri tek tek okunmadı. Örneklerin bir bölümü önceki yapımdan geldiği için aşağıdaki sayılar temizlik sırasındaki durumu gösterir, son setin hata oranı değildir. Son yapımda örnekleme giren 14 kayıt okunmadı.

| Sonuç | Kayıt |
|---|---|
| consistent_with_source | 153 |
| rule_checked | 30 |
| needs_legal_review | 10 |
| reject | 7 |

Reddedilen kayıtlar `qc_rejected_ids_v1.0.txt` dosyasındadır. Bulunan ve kurala çevrilen hatalar: ekli süre ifadeleri (`iki yıldan beş yıla`) kontrol dışı kalıyordu; `(Kaynak: gaiplik-nedir.html)` izleri; Terörle Mücadele Kanunu'nun `TMK` kısaltmasıyla Medeni Kanun sanılması; Tebligat Kanunu atıflarının İİK maddesi sanılması.

## Otomatik kontroller

`pytest tests` her pipeline çalışmasında şunları doğrular: metadata eksiksizliği, benzersiz ID,
boş olmayan alanlar, bozuk karakter, chunk token sınırı, kümeler arası doküman, kaynak dosya, kanun
maddesi ve yakın tekrar sızıntısı, atıf yapılan maddenin varlığı, görev dengesi ve onay bayraklarının
yanlışlıkla açılmaması.

## İnsan incelemesi nasıl yapılır

`kalite_inceleme_v1.0.xlsx` dosyasındaki sarı sütunları doldurun, ardından
`python scripts/qc_review_sheet.py import` ve `python scripts/11_quality_report.py` çalıştırın.
Kaynakla tutarsız kayıtların kimlikleri ekrana yazılır; bunları `qc_rejected_ids_v1.0.txt` dosyasına
ekleyip pipeline'ı 07. adımdan çalıştırın.

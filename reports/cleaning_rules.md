# Temizleme ve filtreleme kuralları

Mevzuat kuralları `scripts/03b_clean_legislation.py`, soru-cevap kuralları `scripts/03_clean.py` ve
`scripts/06_filter_instruction.py` içindedir. Gerçek öncesi-sonrası örnekleri:
[cleaning_examples_v1.0.md](cleaning_examples_v1.0.md).

## Mevzuat

| Kural | Ne yapar | Neden |
|---|---|---|
| Sayfa başlığı silme | Tarih + `Sayfa x / y` + URL satırlarını siler; 1'den sona her sayfa bulunmazsa durur | Her sayfada tekrar eden tarayıcı başlığı |
| Unicode NFC | Karakter varyantlarını tek biçime çeker; NFKC seçilmedi | NFKC `²` gibi işaretleri rakama çevirir, hukuk metninde anlam değiştirebilir |
| Özel karakter | NBSP boşluğa, `ﬁ`/`ﬂ` harflere döner | PDF yazı tipi kalıntısı |
| Kırık kelime onarımı | `ki şi`, `Ba şbakan`, `b aşlangıcı` birleştirilir | PDF, `ş` ve `ğ` önüne boşluk ekliyor |
| Harf aralığı onarımı | `B u K a n u n` sözlükle kelimelere bölünür | İki yana yaslı satırlarda harf aralığı |
| Boşluk normalizasyonu | Satır içi boşluklar teke iner, boş satırlar kalkar | Hizalama boşlukları tokenizer'da gürültü yaratır |
| Satır birleştirme | Küçük harfle başlayan satır öncekine bağlanır | PDF satır kırılması; madde ve bent başları korunur |

**Güvence:** Yukarıdaki kuralların tamamı yalnızca sayfa başlığı siler veya boşluk değiştirir. Her
çalışmada metnin boşluksuz özeti envanterdeki `content_sha256` ile karşılaştırılır. Bir harf veya rakam
değişirse pipeline durur. Sayılar, madde numaraları ve kanun atıfları bu yüzden korunur.

## Soru-cevap kayıtları

`03_clean.py`: HTML entity çözme, HTML etiketi silme, NFC, boşluk normalizasyonu, boş kayıt eleme.

`06_filter_instruction.py` sırasıyla uygular; bir kayıt ilk takıldığı nedenle loglanır:

| Etiket | Elenen kayıt | Gerekçe |
|---|---|---|
| `too_short` / `too_long` / `truncated_answer` | Eşikler `config.yaml` | Anlamlı cevap taşımayan veya kesilmiş kayıtlar |
| `source_artifact` | Metinde site adresi | Kaynak sitenin izi ve üçüncü taraf içerik işareti |
| `personal_data` | E-posta, telefon, IBAN, geçerli TCKN | Kişisel veri corpus'a alınmaz |
| `draft_legislation` | Taslak veya kanun teklifi | Yürürlükte olmayan metin |
| `context_dependent` | `metinde`, `bu makale`, `yukarıdaki` | Soru tek başına anlaşılmıyor veya kaynak metne yaslanıyor |
| `unverifiable_case_law` | Karar numarası veya yüksek mahkeme atfı | Corpus'ta karar metni yok, atıf doğrulanamaz |
| `law_outside_corpus` | 12 kanun dışı atıf | Doğrulanacak metin elde yok |
| `no_resolvable_citation` | Kanun ve madde çözülemedi | Kaynağa bağlanamaz |
| `article_not_found` | Madde kanunda yok | Uydurma veya hatalı atıf riski |
| `repealed_article` | Madde mülga | Güncel olmayan bilgi |
| `low_evidence` | Kanıt skoru < 0,55 | Cevabın kelimeleri atıf yapılan maddede yeterince geçmiyor |
| `numeric_mismatch` | Süre maddede yok | `30 gün` denip maddede `iki hafta` yazması gibi |
| `alternative_answer` | Aynı soruya farklı cevap | Kanıtı en güçlü cevap kalır |
| `near_duplicate` | Soru Jaccard ≥ 0,85 | Kanıtı en güçlü kayıt kalır |

## Eşik gerekçeleri

- **Kanıt skoru 0,55:** Skor dağılımının medyanına yakın (0,54) seçildi, yani atıfı çözülen kayıtların
  yaklaşık yarısı elenir. Eşik el ile etiketlenmiş veriyle kalibre edilmedi. Etkisi sınırlıdır, çünkü final
  seçimde en yüksek skorlu kayıtlar önceliklidir. Skor kelime örtüşmesidir, anlam doğruluğu ölçmez.
- **Jaccard 0,85:** Üç kelimelik parçalar üzerinde. v0.9'daki 308.009 kayıtlık analizde kullanılan eşik
  korundu. LSH adayları gerçek Jaccard ile doğrulanır.
- **Yakın tekrar neden yalnızca seçim aşamasında siliniyor:** Hukukta küçük bir fark (süre, miktar,
  `yapabilir`/`yapamaz`) sonucu değiştirir. Bu yüzden bütün havuzda otomatik silme yapılmadı.

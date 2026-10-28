# LexiTech TR

Türkçe Hukuk Alanı için Veri Mühendisliği ve Yapay Zekâ Veri Seti Hazırlama Projesi.

## Projenin Amacı

LexiTech TR, Türkçe hukuk alanında kullanılabilecek dil modelleri için veri hazırlama, temizleme, kalite denetimi ve veri seti oluşturma süreçlerine odaklanan bir bitirme projesidir.

**Vize kapsamında yalnızca veri mühendisliği yapılmıştır. Model eğitimi gerçekleştirilmemiştir.**

## 1. Domain Corpus v0.9

Resmî mevzuat kaynaklarından elde edilen 12 kanunun metinlerinden hazırlanmıştır.

| Özellik | Değer |
|---|---:|
| Kanun sayısı | 12 |
| Karakter sayısı | 4.471.279 |
| Qwen tokenizer token sayısı | 1.655.887 |
| Sürüm | v0.9 |

Kapsanan kanunlar: Anayasa (2709), Türk Medeni Kanunu (4721), Türk Borçlar Kanunu (6098), Türk Ceza Kanunu (5237), Ceza Muhakemesi Kanunu (5271), İş Kanunu (4857), Türk Ticaret Kanunu (6102), Tüketicinin Korunması Hakkında Kanun (6502), İdari Yargılama Usulü Kanunu (2577), Vergi Usul Kanunu (213), İcra ve İflas Kanunu (2004) ve Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu (5510).

Yapılan işlemler: PDF metin çıkarımı, temizleme, metadata oluşturma, SHA-256 kaydı, token sayımı, belge bazlı train/validation/test ayrımı ve hukuki yapıya duyarlı parçalama.

Ayrıntılar: [DATASET_CARD.md](DATASET_CARD.md)

## 2. Instruction Dataset v0.9

Türkçe hukuk soru-cevaplarından oluşturulan SFT aday veri setidir.

Başlangıç kaynakları:
- sinanelms/hukukisorular
- OrionCAF/turkish_law_qa_dataset

| Aşama | Kayıt sayısı |
|---|---:|
| Başlangıç havuzu | 378.903 |
| Birebir tekrar sonrası | 308.009 |
| Madde göstergeli aday havuzu | 131.045 |
| Güncel teknik ön taslak | 124.510 |

### Veri bölmeleri

| Küme | Kayıt |
|---|---:|
| Train | 111.782 |
| Validation | 6.397 |
| Test | 6.331 |
| **Toplam** | **124.510** |

Kayıtlar soru-cevap içeren `messages` alanı ve kaynak/kalite metadata'sı taşır.

Ayrıntılar: [INSTRUCTION_CARD.md](INSTRUCTION_CARD.md)

## 3. Veri Mühendisliği Süreci

1. Veri kaynaklarının temini ve kayıt altına alınması.
2. PDF metin çıkarımı ve temizleme.
3. Metadata ve belge kimliklerinin oluşturulması.
4. Birebir tekrarların tespit edilmesi.
5. MinHash/LSH ile yakın tekrar analizi.
6. Kanun ve madde atıflarının yapısal denetimi.
7. Alternatif cevapların inceleme havuzuna ayrılması.
8. Kaynak dosyası bazlı train/validation/test bölme.
9. Kümeler arası tekrar ve veri sızıntısı kontrolü.
10. İstatistik ve kalite raporlarının hazırlanması.

## 4. Kalite Denetimi

Güncel Instruction Dataset üzerinde:
- Kümeler arası normalize birebir soru tekrarı: **0**
- Kümeler arası ortak kaynak dosyası: **0**
- Eski MinHash raporundan güncel veri setinde kalan yakın tekrar çifti: **527**
- Bunlardan farklı kümelerde bulunan çift: **0**
- Alternatif cevap incelemesine ayrılan kayıt: **4.630**
- Kümeler arası tekrar nedeniyle ayrılan kayıt: **5**

Bu kontroller, bütün anlamsal tekrarların giderildiği veya cevapların hukuken doğru olduğu anlamına gelmez.

### Manuel değerlendirme

200 örnekten 1 kayıt ek inceleme gerektiriyor, 1 kayıt geçici kabul aldı, 198 kayıt ise henüz değerlendirilmedi.

**Nihai hukuk uzmanı onayı verilmemiştir.**

## 5. Kaynak ve Kullanım Hakları

22 kaynak girdisi kaydedilmiştir:
- 12 resmî mevzuat kaynağı
- 2 üçüncü taraf soru-cevap veri seti
- 8 kaynak olarak belirtilen hukuk sitesi

Kaynakların lisansları, altta yatan içeriklerin hakları ve yeniden dağıtım koşulları için inceleme devam etmektedir.

**Veri setleri eğitim ve yeniden dağıtım için nihai onay almamıştır.**

## 6. Proje Yapısı

Ana klasörler:

- `data/raw/` — Ham veriler
- `data/extracted/` — Çıkarılan metinler
- `data/cleaned/` — Temizlenmiş metinler
- `data/deduplicated/` — Tekrarları ayıklanan veriler
- `data/interim/` — Ara veri setleri
- `data/final/` — Oluşturulan veri dosyaları
- `scripts/` — Veri işleme kodları
- `reports/` — İstatistikler ve denetim raporları

Bazı büyük veri dosyaları ve manuel inceleme materyalleri `.gitignore` kapsamında yerel ortamda tutulur.

## 7. Geliştirme Ortamı

- Python 3.11
- macOS
- JSONL ve CSV
- datasketch / MinHash / LSH
- Hugging Face tokenizer

## 8. Vize Teslim Belgeleri

- [Domain Corpus Kartı](DATASET_CARD.md)
- [Instruction Dataset Kartı](INSTRUCTION_CARD.md)
- [Genel Kalite Raporu](reports/quality/VIZE_DATA_QUALITY_REPORT_v0.9.md)
- [Kaynak Hakları Denetimi](reports/sources/source_rights_audit_v0.9.csv)

## 9. Bilinen Sınırlamalar

- PDF/OCR kaynaklı metin hataları bulunabilir.
- Mevzuat güncelliği ayrıca doğrulanmalıdır.
- Hukuki cevaplar henüz uzman onayından geçmemiştir.
- Bazı hukuk alanlarının test kümesindeki temsili düşüktür.
- Kapsamlı anlamsal yakın tekrar taraması tamamlanmamıştır.
- Kaynak lisansları ve kişisel veri denetimleri açıktır.

## 10. Sonraki Aşamalar

- Manuel kalite değerlendirmelerini tamamlamak.
- Mevzuat güncelliğini kontrol etmek.
- Kaynak kullanım haklarını doğrulamak.
- Yakın tekrar analizini genişletmek.
- Değerlendirme kümelerini iyileştirmek.
- Onaylanan verilerle v1.0 sürümünü hazırlamak.

---

**Proje durumu: v0.9 — Veri mühendisliği ön taslağı.**

Bu proje hukuki danışmanlık hizmeti sunmaz.

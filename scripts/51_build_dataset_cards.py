import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(".")
DOMAIN = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
DOMAIN_SPLITS = Path("data/final/domain_v0.9")
INSTRUCTION = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)

TODAY = date.today().isoformat()
SPLITS = ("train", "validation", "test")


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_card(path, content):
    if path.exists():
        backup = path.with_suffix(".md.backup")
        shutil.copy2(path, backup)
        print("Mevcut dosya yedeklendi:", backup)

    path.write_text(content.strip() + "\n", encoding="utf-8")
    print("Oluşturuldu:", path)


if not DOMAIN.exists():
    raise FileNotFoundError(DOMAIN)

for split in SPLITS:
    path = INSTRUCTION / f"{split}.jsonl"
    if not path.exists():
        raise FileNotFoundError(path)


# DOMAIN CORPUS İSTATİSTİKLERİ
documents = list(read_jsonl(DOMAIN))

domain_count = len(documents)
domain_tokens = sum(
    int(d.get("token_count", 0))
    for d in documents
)
domain_chars = sum(
    int(d.get("char_count", len(d.get("text", ""))))
    for d in documents
)

law_titles = sorted(
    (
        str(d["law_number"]),
        str(d["title"])
    )
    for d in documents
)

domain_split_counts = {}

for split in SPLITS:
    path = DOMAIN_SPLITS / f"{split}.jsonl"
    domain_split_counts[split] = (
        sum(1 for _ in read_jsonl(path))
        if path.exists() else None
    )


# INSTRUCTION İSTATİSTİKLERİ
instruction_counts = Counter()
instruction_laws = Counter()
law_by_split = {
    split: Counter()
    for split in SPLITS
}
sources = Counter()
unapproved = 0
rights_pending = 0

for split in SPLITS:
    for record in read_jsonl(
        INSTRUCTION / f"{split}.jsonl"
    ):
        instruction_counts[split] += 1

        metadata = record["metadata"]
        law = str(metadata["law_indicator"])

        instruction_laws[law] += 1
        law_by_split[split][law] += 1
        sources[str(metadata["source"])] += 1

        if metadata.get("training_approved") is False:
            unapproved += 1

        if metadata.get("rights_status") == "pending_review":
            rights_pending += 1

instruction_total = sum(instruction_counts.values())

if domain_count != 12:
    raise ValueError(
        f"12 domain belgesi bekleniyordu: {domain_count}"
    )

if instruction_total != 124510:
    raise ValueError(
        f"124510 QA bekleniyordu: {instruction_total}"
    )


law_lines = "\n".join(
    f"- **{law}:** {title}"
    for law, title in law_titles
)

domain_card = f"""
# LexiTech TR — DATASET_CARD

**Sürüm:** Domain Corpus v0.9 (ön taslak)
**Belge tarihi:** {TODAY}
**Dil:** Türkçe
**Alan:** Türkiye hukuku
**Durum:** Hukuki içerik ve kullanım hakları için nihai onay bekleniyor.

## 1. Amaç

Türkçe hukuk alanına uyarlanacak dil modelleri için
alan korpusu oluşturmak. Bu korpus ileriki aşamada
CPT/DAPT çalışmaları için aday veri sağlayabilir.

**Vize aşamasında model eğitimi gerçekleştirilmemiştir.**

## 2. Veri kapsamı

- Belge sayısı: **{domain_count}**
- Toplam karakter: **{domain_chars:,}**
- Toplam tokenizer tokenı: **{domain_tokens:,}**
- Kaynak türü: Resmî mevzuat PDF belgelerinden çıkarılan metinler.
- Tokenizer: `Qwen/Qwen2.5-3B-Instruct`.
- Birim: Kanun belgesi; ayrıca parçalama (chunking)
  sürümleri hazırlanmıştır.

### Kapsanan kanunlar

{law_lines}

## 3. Veri kaynakları ve izlenebilirlik

Kaynak listesi:

`reports/sources/legislation_documents.csv`

Bu listede mevcut kaynak bilgileri, erişim tarihleri ve
SHA-256 değerleri saklanmaktadır.

Resmî mevzuat PDF'lerinin kullanılmış olması, her türlü
yeniden dağıtım veya model eğitimi için kullanım haklarının
otomatik olarak onaylandığı anlamına gelmez.

**Kullanım hakları durumu: İnceleme bekliyor.**

## 4. Veri hazırlama işlemleri

1. PDF belgelerinin temin edilmesi.
2. Metin çıkarımı ve otomatik metin temizliği.
3. Belge kimliği, kaynak ve SHA-256 metadata'sının kaydı.
4. Tokenizer ile token sayılarının hesaplanması.
5. Belge bazlı train/validation/test ayrımı.
6. Ana kanun, işlenmemiş hükümler ve değişiklik
   tablolarına yönelik bölümleme.
7. Token sınırını gözeten hukuki duyarlı parçalama.
8. Parça bütünlüğü ve yakın tekrar denetimleri.

## 5. Bölme yaklaşımı

Kanun belgeleri belge düzeyinde ayrılmıştır.

- Train belge sayısı: {domain_split_counts['train']}
- Validation belge sayısı: {domain_split_counts['validation']}
- Test belge sayısı: {domain_split_counts['test']}

Bu ayrımda farklı splitlerde aynı kanun belgesi bulunmaz.

**Sınırlama:** Validation ve test kümeleri yalnızca
birer kanundan oluşmaktadır. Dolayısıyla tüm hukuk
alanlarını temsil eden dengeli bir değerlendirme
sağladıkları iddia edilemez.

## 6. Veri biçimi

- Belge düzeyi:
  `data/final/domain_corpus_v0.9_tokenized.jsonl`
- Belge splitleri:
  `data/final/domain_v0.9/`
- Hukuki duyarlı chunk splitleri:
  `data/final/domain_v0.9/chunks_legal_aware/`

Örnek metadata alanları:

`document_id`, `law_number`, `title`, `source_url`,
`raw_sha256`, `text_sha256`, `token_count`,
`rights_status`, `quality_status`.

## 7. Kalite ve bilinen riskler

- PDF çıkarımından kaynaklanabilen OCR, harf,
  kelime aralığı ve madde numarası hataları.
- Belge sürümlerinin güncelliğinin ayrıca
  doğrulanması gerekliliği.
- Değişiklik tablolarının model eğitimine doğrudan
  alınmaması gerekliliği.
- Hukuki duyarlı chunking işleminde bazı uzun
  maddelerin bölünmüş olması.
- Otomatik temizliğin hukuk uzmanı onayı yerine
  geçmemesi.
- Kaynak belgelerin güncel ve yürürlükteki metinlerle
  karşılaştırılmasının tamamlanmamış olması.

Chunk metadata'sındaki `requires_manual_review`
ve `training_candidate` alanları dikkate alınmalıdır.

## 8. Kalite kanıtları

- `reports/statistics/domain_token_summary_v0.9.json`
- `reports/quality/domain_chunk_final_comparison_v0.9.json`
- `reports/statistics/domain_chunk_stats_legal_aware_v0.9.json`
- `reports/quality/domain_section_plan_v0.9.csv`
- `reports/quality/domain_corpus_near_duplicate_pairs_v0.9.csv`

## 9. İnsan değerlendirmesi

Alan korpusu için hedeflenen kapsamlı manuel
örnek incelemesi ve nihai hukuki uzman onayı
henüz tamamlanmamıştır.

## 10. Kullanım sınırları

Bu veri seti **v0.9 teknik ön taslaktır**.

Kaynakların izin durumu, metin güncelliği, hukuki
doğruluk ve insan kalite değerlendirmesi tamamlanmadan
`v1.0` veya eğitim için onaylanmış veri olarak
sunulmamalıdır.
"""

source_lines = "\n".join(
    f"- `{source}`: {count:,} kayıt"
    for source, count in sorted(sources.items())
)

distribution_header = (
    "| Kanun | Train | Validation | Test | Toplam |\n"
    "|---|---:|---:|---:|---:|"
)

distribution_rows = "\n".join(
    f"| {law} | "
    f"{law_by_split['train'][law]:,} | "
    f"{law_by_split['validation'][law]:,} | "
    f"{law_by_split['test'][law]:,} | "
    f"{instruction_laws[law]:,} |"
    for law in sorted(instruction_laws)
)

instruction_card = f"""
# LexiTech TR — INSTRUCTION_CARD

**Sürüm:** Instruction Dataset v0.9 (ön taslak)
**Belge tarihi:** {TODAY}
**Dil:** Türkçe
**Alan:** Türkiye hukuku
**Durum:** Eğitim için onaylanmadı.

## 1. Amaç

Türkçe hukuk soru-cevap biçimindeki instruction verilerini,
ileriki SFT çalışmaları için incelemek ve hazırlamak.

**Vize aşamasında model eğitimi gerçekleştirilmemiştir.**

## 2. Kaynaklar

İlk havuzda iki Hugging Face kaynağı değerlendirilmiştir:

- `sinanelms/hukukisorular`
- `OrionCAF/turkish_law_qa_dataset`

Başlangıç havuzu: **378.903 kayıt**.
Birebir tekrar giderilmiş ilk havuz: **308.009 kayıt**.
Madde göstergeli inceleme havuzu: **131.045 kayıt**.

Güncel ön taslaktaki kaynaklar:

{source_lines}

Kaynaklara ait kullanım lisansları ve veri üretim
kökenleri **ayrıca doğrulanmalıdır**.

Kaynakta görülen `0.json`, `24.json` benzeri etiketler,
**resmî kanun belgesi kimliği değildir**.

## 3. Güncel veri kümesi

Toplam: **{instruction_total:,}** soru-cevap kaydı.

- Train: **{instruction_counts['train']:,}**
- Validation: **{instruction_counts['validation']:,}**
- Test: **{instruction_counts['test']:,}**

Dosyalar:

- `data/interim/instruction_leakage_clean_v0.9/train.jsonl`
- `data/interim/instruction_leakage_clean_v0.9/validation.jsonl`
- `data/interim/instruction_leakage_clean_v0.9/test.jsonl`

Bunlar **ara aşama veri dosyalarıdır**; eğitim onayı
verilmiş nihai dosyalar değildir.

### Kanun bazında dağılım

{distribution_header}
{distribution_rows}

## 4. Veri şeması

Her kayıt şu alanları taşır:

- `id`
- `messages`: `user` sorusu ve `assistant` cevabı
- `metadata`: dil, kanun göstergesi, kaynak,
  kaynak dosya etiketi, split ve kalite bayrakları.

Kalite bayrakları arasında:

- `training_approved: false`
- `legal_accuracy_verified: false`
- `citation_accuracy_verified: false`
- `rights_status: pending_review`

Bu alanlar, otomatik işlemin hukuki doğrulama
yerine geçmediğini açıkça gösterir.

## 5. Seçim ve filtreleme

1. Kaynakların normalize edilmesi.
2. İlk birebir tekrarların kaldırılması.
3. Kanun ve madde göstergeleriyle aday havuzu oluşturulması.
4. Madde numarası yapısal kontrolü.
5. Şüpheli atıfların ve köken bilgisi yetersiz
   kayıtların geçici olarak ayrılması.
6. Kaynak dosya ve aynı soru bağlantılarına dayanan
   belge gruplu split planı.
7. Aynı sorunun alternatif cevap versiyonlarının
   inceleme havuzuna ayrılması.
8. Normalize edilmiş kümeler arası birebir soru
   sızıntısının giderilmesi.
9. Önceden belirlenmiş MinHash yakın tekrar çiftlerinin
   güncel veri setiyle karşılaştırılması.

## 6. Kayıt muhasebesi

Madde göstergeli havuz: **131.045**

- Şüpheli atıf nedeniyle ayrılan: **933**
- Kaynak kökeni yetersiz OrionCAF adayları: **960**
- İlk splitli ön taslak: **129.152**
- Alternatif cevaplı kayıtlar: **4.630**
- Eşdeğer tekrar nedeniyle atlanan kayıtlar: **7**
- Kümeler arası normalize soru tekrarı nedeniyle
  ayrılan kayıtlar: **5**
- Güncel ön taslak: **{instruction_total:,}**

Bu eleme gerekçeleri **hukuki doğruluk kararları
olarak yorumlanmamalıdır**.

## 7. Split ve sızıntı denetimi

- İlk plan: Kaynak dosya bağlantılı 74 grup.
- En büyük bağlantılı grup: 97.033 kayıt.
- Güncel splitlerde ortak kaynak dosya sayısı: **0**.
- Kontrol edilen normalize soru düzeyinde ortak
  train/validation/test soru sayısı: **0**.
- Eski MinHash raporundan güncel veri setinde
  kalan yakın tekrar çifti: **527**.
- Bunların farklı splitlerde bulunanı: **0**.
- Aynı split içindeki çiftler: **527**.

Önceki MinHash yöntemi soru **ve cevabı birlikte**
karşılaştırmış, üç kelimelik parçalar ve 0,85
Jaccard eşiği kullanmıştır.

**Sınırlama:** Güncel veri üzerinde yalnızca soru
metnine dayanan kapsamlı yeni yakın tekrar taraması
yapılmadı. Dolayısıyla sıfır sızıntı garantisi yoktur.

## 8. Dengesizlikler

Veriler özellikle Türk Ceza Kanunu ve Ceza
Muhakemesi Kanunu soruları bakımından yoğunlaşmaktadır.

İş Kanunu, sosyal sigorta, ticaret ve tüketici
hukuku alanlarında validation/test örneği
sayısı bazı kümelerde çok düşüktür.

Bu kümelerle her hukuk alanında aynı güvenilirlikte
performans ölçümü yapıldığı iddia edilmemelidir.

## 9. İnsan değerlendirmesi

200 soruluk tabakalı manuel değerlendirme örneklemi:

`reports/quality/instruction_manual_review_200_v0.9.csv`

Mevcut ilerleme:

- 1 kayıt: Ek inceleme gerekli.
- 1 kayıt: Geçici kabul.
- 198 kayıt: Henüz değerlendirilmedi.

**Nihai hukuk uzmanı onayı verilmedi.**

Örneklem kanun bazında tabakalıdır; genel veri
kümesinin rastgele ve temsili örneklemi değildir.

## 10. Hukuki ve etik riskler

- Yanlış kanun-madde eşleştirmeleri.
- Gerçekte doğrulanmamış yargı kararı atıfları.
- Tarihi geçmiş veya mevzuat değişikliklerinden
  etkilenmiş cevaplar.
- Farklı cevap versiyonlarında eksik bilgi ve
  olası hukuki çelişkiler.
- Otomatik hazırlanmış veya üretim kökeni
  belirsiz kaynak metinleri.
- Kaynak lisanslarının ve kullanım izinlerinin
  henüz netleşmemiş olması.
- Soru-cevaplar üzerinden gerçek kişilere ilişkin
  kişisel veri risklerinin ayrıca incelenmesi gereği.

**Madde numarasının ilgili kanunda bulunması,
cevabın hukuken doğru olduğunu göstermez.**

## 11. İlgili denetim raporları

- `reports/quality/instruction_article_audit_v0.9.json`
- `reports/quality/instruction_reference_mismatches_v0.9.csv`
- `reports/splits/instruction_split_plan_v0.9.json`
- `reports/quality/instruction_split_integrity_v0.9.json`
- `reports/quality/instruction_dedup_report_v0.9.json`
- `reports/quality/instruction_balance_audit_v0.9.json`
- `reports/quality/instruction_leakage_fix_v0.9.json`
- `reports/quality/instruction_existing_near_duplicates_v0.9.json`

## 12. Eğitim ve paylaşım kısıtları

Güncel ön taslaktaki **{unapproved:,}** kayıtta
`training_approved: false` bulunmaktadır.

**{rights_pending:,}** kaydın kullanım hakkı durumu
`pending_review` olarak işaretlidir.

Kaynak kullanım izinleri, kişisel veri incelemesi
ve hukuki kalite denetimleri tamamlanmadan
bu veri seti `v1.0` veya eğitim için onaylı
olarak sunulmamalıdır.
"""

write_card(Path("DATASET_CARD.md"), domain_card)
write_card(Path("INSTRUCTION_CARD.md"), instruction_card)

print("\nLEXITECH TR - VERİ SETİ KARTLARI")
print("=" * 55)
print("Domain belgesi:", domain_count)
print("Domain token:", f"{domain_tokens:,}")
print("Instruction kayıt:", f"{instruction_total:,}")
print("Eğitim onayı olmayan:", f"{unapproved:,}")
print("Kullanım hakkı incelemesi bekleyen:", f"{rights_pending:,}")
print("Durum: İki kart oluşturuldu; nihai onay verilmedi.")

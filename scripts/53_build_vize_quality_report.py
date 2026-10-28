import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPORT_PATH = Path(
    "reports/quality/VIZE_DATA_QUALITY_REPORT_v0.9.md"
)

JSON_PATH = Path(
    "reports/quality/vize_quality_summary_v0.9.json"
)

INSTRUCTION_DIR = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)

DOMAIN_FILE = Path(
    "data/final/domain_corpus_v0.9_tokenized.jsonl"
)

MANUAL_FILE = Path(
    "reports/quality/instruction_manual_review_200_v0.9.csv"
)

RIGHTS_FILE = Path(
    "reports/sources/source_rights_audit_v0.9.csv"
)

SPLITS = ("train", "validation", "test")


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def number(value):
    return f"{value:,}".replace(",", ".")


# 1. Domain Corpus
domain_docs = list(read_jsonl(DOMAIN_FILE))
domain_tokens = sum(
    int(doc.get("token_count", 0))
    for doc in domain_docs
)
domain_chars = sum(
    int(doc.get("char_count", len(doc.get("text", ""))))
    for doc in domain_docs
)
domain_laws = sorted(
    str(doc["law_number"])
    for doc in domain_docs
)

# 2. Instruction Dataset
split_counts = Counter()
law_by_split = defaultdict(Counter)
source_counts = Counter()
not_approved = 0
rights_pending = 0

for split in SPLITS:
    for record in read_jsonl(
        INSTRUCTION_DIR / f"{split}.jsonl"
    ):
        split_counts[split] += 1
        metadata = record["metadata"]

        law_by_split[str(metadata["law_indicator"])][split] += 1
        source_counts[str(metadata["source"])] += 1

        if metadata.get("training_approved") is False:
            not_approved += 1

        if metadata.get("rights_status") == "pending_review":
            rights_pending += 1

instruction_total = sum(split_counts.values())

# 3. Existing audit reports
initial_split = read_json(
    Path("reports/quality/instruction_split_integrity_v0.9.json")
)
dedup = read_json(
    Path("reports/quality/instruction_dedup_report_v0.9.json")
)
balance = read_json(
    Path("reports/quality/instruction_balance_audit_v0.9.json")
)
leakage = read_json(
    Path("reports/quality/instruction_leakage_fix_v0.9.json")
)
near = read_json(
    Path("reports/quality/instruction_existing_near_duplicates_v0.9.json")
)
article = read_json(
    Path("reports/quality/instruction_article_audit_v0.9.json")
)

manual_rows = read_csv(MANUAL_FILE)
manual_counts = Counter(
    (row.get("overall_decision") or "pending").strip()
    for row in manual_rows
)

rights_rows = read_csv(RIGHTS_FILE)
rights_types = Counter(
    row["source_type"]
    for row in rights_rows
)
rights_approved = sum(
    row["training_approved"].strip().lower() == "true"
    for row in rights_rows
)

# 4. Checks
checks = {
    "domain_document_count_12": len(domain_docs) == 12,
    "instruction_total_124510": instruction_total == 124510,
    "manual_sample_200": len(manual_rows) == 200,
    "split_integrity_pass": initial_split["status"] == "PASS",
    "leakage_fix_pass": leakage["status"] == "PASS",
    "cross_split_documents_zero": (
        leakage["cross_split_source_documents_after"] == 0
    ),
    "cross_split_normalized_questions_zero": (
        leakage["cross_split_groups_after"] == 0
    ),
    "near_pair_reconciliation": (
        near["counts"]["pairs_both_retained"]
        + near["counts"]["pairs_not_fully_retained"]
        == near["counts"]["old_near_duplicate_pairs"]
    ),
    "all_instruction_training_unapproved": (
        not_approved == instruction_total
    ),
    "all_instruction_rights_pending": (
        rights_pending == instruction_total
    ),
}

failed = [
    key
    for key, passed in checks.items()
    if not passed
]

if failed:
    print("Rapor oluşturulmadı; beklenmeyen sonuçlar:")
    for key in failed:
        print(" -", key)
    raise SystemExit(1)

# 5. Markdown tables
law_table = [
    "| Kanun | Train | Validation | Test | Toplam |",
    "|---|---:|---:|---:|---:|",
]

for law in sorted(law_by_split):
    counts = law_by_split[law]
    total = sum(counts.values())

    law_table.append(
        f"| {law} | "
        f"{number(counts['train'])} | "
        f"{number(counts['validation'])} | "
        f"{number(counts['test'])} | "
        f"{number(total)} |"
    )

source_table = [
    "| Kaynak türü | Kayıt sayısı |",
    "|---|---:|",
]

for source_type, count in sorted(rights_types.items()):
    source_table.append(
        f"| {source_type} | {number(count)} |"
    )

manual_table = [
    "| Manuel inceleme durumu | Kayıt sayısı |",
    "|---|---:|",
]

for status, count in sorted(manual_counts.items()):
    manual_table.append(
        f"| {status} | {number(count)} |"
    )

near_counts = near["counts"]
dedup_counts = dedup["counts"]

text = f"""
# LexiTech TR — Vize Veri Kalitesi Raporu

**Rapor sürümü:** v0.9
**Tarih:** {date.today().isoformat()}
**Çalışma alanı:** Türkçe hukuk yapay zekâsı
**Aşama:** Veri mühendisliği ve kalite denetimi

## 1. Yönetici özeti

Bu çalışma, Türkçe hukuk alanında kullanılabilecek iki
veri setinin teknik ön taslaklarını hazırlamıştır:

1. **Domain Corpus v0.9:** Resmî mevzuat metinlerinden
   oluşturulan alan korpusu.
2. **Instruction Dataset v0.9:** Türkçe hukuk
   soru-cevap kayıtlarından oluşturulan SFT aday havuzu.

**Bu aşamada model eğitimi yapılmamıştır.**

Teknik veri hazırlama ve bazı otomatik bütünlük kontrolleri
tamamlanmış olsa da, kaynak kullanım hakları, kapsamlı
insan değerlendirmesi ve hukuk uzmanı doğrulaması
tamamlanmamıştır.

Bu nedenle iki veri seti de henüz eğitim için
onaylanmış `v1.0` sürümü değildir.

## 2. Domain Corpus sonuçları

| Ölçüt | Sonuç |
|---|---:|
| Kanun belgesi | {number(len(domain_docs))} |
| Farklı kanun numarası | {number(len(set(domain_laws)))} |
| Karakter | {number(domain_chars)} |
| Qwen tokenizer tokenı | {number(domain_tokens)} |

**Kanun numaraları:** {", ".join(domain_laws)}

Korpusun belge bazlı train/validation/test dosyaları
ve hukuki duyarlı chunk sürümü hazırlanmıştır.

İlgili dosyalar:

- `data/final/domain_corpus_v0.9_tokenized.jsonl`
- `data/final/domain_v0.9/`
- `data/final/domain_v0.9/chunks_legal_aware/`
- `DATASET_CARD.md`

### Domain Corpus sınırlamaları

- PDF'den metin çıkarımına bağlı hatalar bulunabilir.
- Kanunların güncelliği ve yürürlükteki sürümleri
  ayrıca karşılaştırılmalıdır.
- Değişiklik tabloları doğrudan eğitim verisi
  kabul edilmemelidir.
- Validation/test ayrımı hukuk alanları açısından
  yeterince temsili değildir.
- Kapsamlı manuel kalite kontrolü tamamlanmamıştır.

## 3. Instruction Dataset hazırlama süreci

| İşlem | Kayıt |
|---|---:|
| İlk iki kaynak toplamı | 378.903 |
| Birebir tekrar sonrası ilk havuz | 308.009 |
| Madde göstergeli aday havuzu | 131.045 |
| Atıf incelemesine ayrılan | 933 |
| Kaynak bilgisi nedeniyle ayrılan OrionCAF adayı | 960 |
| İlk bölünmüş veri seti | 129.152 |
| Farklı cevaplı soru versiyonları (inceleme havuzu) | 4.630 |
| Eşdeğer soru-cevap tekrarı | 7 |
| Kümeler arası normalize soru tekrarı | 5 |
| **Güncel ön taslak** | **{number(instruction_total)}** |

Bu kayıtların ayrılması, içeriklerinin kesin olarak
yanlış olduğuna ilişkin bir karar değildir.

### Güncel train/validation/test sayıları

| Küme | Kayıt |
|---|---:|
| Train | {number(split_counts['train'])} |
| Validation | {number(split_counts['validation'])} |
| Test | {number(split_counts['test'])} |
| **Toplam** | **{number(instruction_total)}** |

### Kanun bazında dağılım

{chr(10).join(law_table)}

### Veri bölme ve sızıntı kontrolleri

- Kaynak dosyası temelli bölme uygulanmıştır.
- Güncel kümeler arasında ortak kaynak dosyası: **0**.
- Kontrol edilen normalize soru metnine göre
  kümeler arası birebir tekrar: **0**.
- İlk bölme bütünlük kontrolü: **PASS**.
- Sızıntı düzeltme kontrolü: **PASS**.

**Sınırlama:** Aynı anlama gelen fakat farklı
kelimelerle yazılmış bütün soruların tespit edildiği
iddia edilmemektedir.

### Yakın tekrar denetimi

Önceki MinHash analizi 308.009 kayıt üzerinde
yürütülmüştür. Yöntem soru ve cevap metnini birlikte
karşılaştırmış, üç kelimelik shingles ve 0,85
Jaccard eşiği kullanmıştır.

Güncel veri setinde, önceki rapordaki çiftlerden:

- İki kaydı da kalan çift: **{number(near_counts['pairs_both_retained'])}**
- Aynı split içinde kalan çift: **{number(near_counts['within_split_pairs'])}**
- Farklı splitlerde kalan çift: **{number(near_counts.get('cross_split_pairs', 0))}**

Bu sonuçlar **yalnızca eski MinHash raporunda
tespit edilmiş çiftler** için geçerlidir.
Güncel soru metinleri üzerinde kapsamlı yeni bir
yakın tekrar taraması yapılmamıştır.

### Dengeli değerlendirme sınırlaması

İş Kanunu, sosyal sigortalar, ticaret ve tüketici
hukuku için validation/test örneği sayıları
düşüktür. Özellikle küçük test gruplarından
güvenilir kanun bazlı performans sonucu
çıkarılmamalıdır.

## 4. Madde atıfları ve hukuki doğruluk

İlk aday havuzunda otomatik olarak incelenen
kayıt sayısı: **{number(article['total'])}**.

Madde numarası yapısal kontrolde:

- Hedef kanun metninde numaraları bulunan:
  **{number(article['status_counts'].get('numbers_present_in_target_law', 0))}**
- Ek atıf incelemesi gerektiren:
  **{number(article['status_counts'].get('requires_reference_review', 0))}**

Madde numarasının bir kanunda bulunması,
cevabın doğru, güncel veya uygun biçimde
kaynaklandırılmış olduğunu kanıtlamaz.

Bazı cevaplarda farklı kanunlara yapılan
atıflar veya başka bir kanun numarasının
madde numarası olarak algılanması söz konusudur.

## 5. Manuel kalite değerlendirmesi

Örneklem dosyası:

`reports/quality/instruction_manual_review_200_v0.9.csv`

Toplam örnek: **{number(len(manual_rows))}**.

{chr(10).join(manual_table)}

İlk iki kayda ilişkin değerlendirmeler **ön niteliktedir**.
Nihai hukuk uzmanı onayı verilmemiştir.

Örneklem kanun bazında tabakalı olarak oluşturulmuştur.
Bu nedenle doğrudan tüm veri setinin hata oranını
tahmin eden temsili bir rastgele örneklem
olarak kullanılmamalıdır.

## 6. Kaynak ve kullanım hakları

Kaynak hakları denetim dosyası:

`reports/sources/source_rights_audit_v0.9.csv`

Toplam kayıtlı kaynak girdisi: **{number(len(rights_rows))}**.

{chr(10).join(source_table)}

Eğitim için açıkça onaylanmış kaynak sayısı:
**{number(rights_approved)}**.

Instruction Dataset içinde:

- `training_approved: false`:
  **{number(not_approved)}** kayıt.
- `rights_status: pending_review`:
  **{number(rights_pending)}** kayıt.

Bir kaynak için onay kaydı bulunmaması,
kullanımın kesinlikle yasak olduğunu göstermez.
İzin durumu henüz yeterli kanıtla
doğrulanmamıştır.

Kaynakların yayımlanan lisans beyanları ile
altta yatan metinlerin hakları ayrı
değerlendirilmelidir.

## 7. Bilinen riskler

1. Hukuki doğruluk ve güncellik hataları.
2. Yanlış veya doğrulanmamış kanun-madde atıfları.
3. Kaynağı doğrulanmamış yargı kararı atıfları.
4. Yakın anlamlı soru tekrarlarının devam etmesi.
5. Ceza hukuku ağırlıklı veri dağılımı.
6. Yetersiz hukuk alanı temsili olan test kümeleri.
7. PDF/OCR kaynaklı metin bozulmaları.
8. Telif ve kullanım izinlerinin tamamlanmamış olması.
9. Kişisel veri taramasının ayrıca yapılması gerekliliği.
10. Manuel uzman kontrolünün büyük ölçüde beklemesi.

## 8. Vize sonrası / v1.0 öncesi işler

- [ ] Domain Corpus'tan 100–200 belgenin veya uygun
      değerlendirme biriminin manuel örnek incelemesi.
- [ ] Instruction Dataset'ten 150–200 örneğin
      planlı manuel kalite değerlendirmesi.
- [ ] Kanunların güncel metinlerle karşılaştırılması.
- [ ] Üçüncü taraf veri kaynaklarının lisans ve
      izin kanıtlarının tamamlanması.
- [ ] Kişisel veri ve hassas içerik kontrolü.
- [ ] Soru odaklı yakın tekrar / sızıntı analizi.
- [ ] Eksik hukuk alanları için güvenilir
      değerlendirme örneklerinin artırılması.
- [ ] Kalite sorunları giderildikten sonra
      nihai eğitim adaylarının belirlenmesi.
- [ ] `v1.0` veri seti kartlarının güncellenmesi.

## 9. İlgili belgeler

- `DATASET_CARD.md`
- `INSTRUCTION_CARD.md`
- `reports/sources/source_rights_audit_v0.9.csv`
- `reports/quality/instruction_split_integrity_v0.9.json`
- `reports/quality/instruction_dedup_report_v0.9.json`
- `reports/quality/instruction_balance_audit_v0.9.json`
- `reports/quality/instruction_leakage_fix_v0.9.json`
- `reports/quality/instruction_existing_near_duplicates_v0.9.json`
- `reports/quality/instruction_manual_review_200_v0.9.csv`

## 10. Sonuç

LexiTech TR vize aşamasında iki farklı amaç için
veri hazırlama altyapısı oluşturulmuştur.

**Teknik kazanım:** Ayrı veri setleri, metadata,
token sayımı, bölümleme, tekrar kontrolleri,
kaynak bazlı split ve denetim raporları.

**Henüz tamamlanmayan:** İnsan ve hukuk uzmanı
onayı, lisans kanıtları, güncellik doğrulaması
ve kapsamlı anlamsal yakın tekrar denetimi.

Bu çalışma, tamamlanmış ve eğitim için onaylanmış
bir hukuk modeli veya nihai `v1.0` veri seti
olarak sunulmamaktadır.
"""

summary = {
    "version": "v0.9",
    "date": date.today().isoformat(),
    "domain": {
        "documents": len(domain_docs),
        "tokens": domain_tokens,
        "characters": domain_chars
    },
    "instruction": {
        "total": instruction_total,
        "splits": dict(split_counts),
        "not_training_approved": not_approved,
        "rights_pending": rights_pending
    },
    "manual_review": dict(manual_counts),
    "source_entries": len(rights_rows),
    "source_types": dict(rights_types),
    "checks": checks,
    "status": "provisional_quality_report"
}

REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

REPORT_PATH.write_text(
    text.strip() + "\n",
    encoding="utf-8"
)

JSON_PATH.write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("LEXITECH TR - VİZE KALİTE RAPORU")
print("=" * 60)
print("Domain belgesi:", len(domain_docs))
print("Domain token:", number(domain_tokens))
print("Instruction kaydı:", number(instruction_total))
print("Kaynak girdisi:", len(rights_rows))
print("Manuel örnek:", len(manual_rows))
print("Başarılı otomatik kontrol:", sum(checks.values()))
print("Başarısız otomatik kontrol:", len(failed))
print("Markdown raporu:", REPORT_PATH)
print("JSON özeti:", JSON_PATH)
print("Durum: v0.9, nihai eğitim onayı yok.")

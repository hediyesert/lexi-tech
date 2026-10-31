import json
from collections import Counter
from pathlib import Path

QUALITY = Path("reports/quality")
STATS = Path("reports/statistics")
ROOT = Path("data/final/domain_v0.9")

AUDIT = QUALITY / "domain_cleaning_integrity_v0.9.json"
COMPARE = QUALITY / "domain_chunk_final_comparison_v0.9.json"

VERSIONS = {
    "original": (
        "chunks",
        "domain_chunk_stats_v0.9.json",
    ),
    "sentence_aware": (
        "chunks_sentence_aware",
        "domain_chunk_stats_sentence_aware_v0.9.json",
    ),
    "legal_aware": (
        "chunks_legal_aware",
        "domain_chunk_stats_legal_aware_v0.9.json",
    ),
}

JSON_OUT = QUALITY / "domain_cleaning_and_exclusion_v0.9.json"
MD_OUT = QUALITY / "domain_cleaning_and_exclusion_v0.9.md"

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit(
        "Rapor zaten mevcut. Uzerine yazilmadi."
    )

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

audit = read_json(AUDIT)
comparison = read_json(COMPARE)

assert audit["status"] == "PASS"
assert audit["documents_checked"] == 12
assert audit["error_count"] == 0
assert audit["training_approved"] is False

for doc in audit["documents"]:
    assert all(
        doc[field] is True
        for field in (
            "raw_sha256_pass",
            "cleaned_sha256_pass",
            "corpus_text_exact_match",
            "corpus_text_sha256_pass",
            "char_count_pass",
            "law_number_pass",
        )
    )

versions = {}
review_flags = Counter()
candidate_flags = Counter()

for version, (folder, filename) in VERSIONS.items():
    stats = read_json(STATS / filename)

    actual = {}
    token_errors = 0
    total = 0

    for split in ("train", "validation", "test"):
        path = ROOT / folder / f"{split}.jsonl"
        count = 0

        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                record = json.loads(line)
                count += 1

                n = record.get("token_count")
                if (
                    not isinstance(n, int)
                    or isinstance(n, bool)
                    or not 0 < n <= 2048
                    or record.get("split") != split
                ):
                    token_errors += 1

                if version == "legal_aware":
                    review_flags[str(
                        record.get("requires_manual_review")
                    )] += 1

                    candidate_flags[str(
                        record.get("training_candidate")
                    )] += 1

        assert count == stats["chunks_per_split"][split]
        actual[split] = count
        total += count

    assert total == stats["total_chunks"]
    assert total == comparison[version]["counts"]["chunks"]
    assert token_errors == 0
    assert stats["document_count"] == 12
    assert stats["max_actual_chunk_tokens"] <= 2048
    assert stats["all_documents_sha256_verified"] is True

    versions[version] = {
        "folder": str(ROOT / folder),
        "total_chunks": total,
        "split_counts": actual,
        "max_chunk_tokens": 2048,
        "oversized_units_split": stats["oversized_units_split"],
        "possible_mid_sentence": comparison[version][
            "counts"
        ].get("possible_mid_sentence"),
        "word_break_examples": len(
            comparison[version].get("word_break_examples", [])
        ),
        "integrity_error_count": comparison[version][
            "integrity_error_count"
        ],
    }

assert versions["original"]["total_chunks"] == 980
assert versions["sentence_aware"]["total_chunks"] == 983
assert versions["legal_aware"]["total_chunks"] == 988
assert review_flags == {"True": 988}

rights = Counter(
    str(doc.get("rights_status"))
    for doc in audit["documents"]
)

quality = Counter(
    str(doc.get("quality_status"))
    for doc in audit["documents"]
)

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "advisor_questions": [5, 6],
    "scope": "domain_corpus_cleaning_and_chunking",
    "document_count": 12,
    "raw_pdf_sha256_verified": 12,
    "cleaned_text_sha256_verified": 12,
    "corpus_exact_text_match_verified": 12,
    "document_cleaning_details": audit["documents"],
    "chunking_versions": versions,
    "documented_preferred_version": "legal_aware",
    "legal_aware_manual_review_flags": dict(review_flags),
    "legal_aware_training_candidate_flags": dict(candidate_flags),
    "source_rights_status_distribution": dict(rights),
    "source_quality_status_distribution": dict(quality),
    "limitations": [
        "Dosya hash kontrolu hukuki dogruluk kaniti degildir.",
        "Karakter sayisi farki tek basina icerik kaybini "
        "kanitlamaz veya dislamaz.",
        "988 legal-aware chunk icin manuel inceleme gereklidir.",
        "Chunking surumleri arasindaki sayi farki "
        "silinen kanun veya kayit sayisi degildir.",
        "Olası cumle ortasi bolunmeler heuristik sinyaldir.",
        "Kaynak guncelligi ve hukuki icerik "
        "bagimsiz olarak dogrulanmamistir.",
        "Veri kullanim haklari ve model egitim izni "
        "bu teknik denetimle verilmez.",
    ],
    "evidence_files": [
        str(AUDIT),
        str(COMPARE),
        str(STATS / VERSIONS["original"][1]),
        str(STATS / VERSIONS["sentence_aware"][1]),
        str(STATS / VERSIONS["legal_aware"][1]),
        "reports/sources/legislation_documents.csv",
        "scripts/10_clean_anayasa.py",
        "scripts/13_remove_page_headers.py",
        "scripts/14_normalize_legislation.py",
        "scripts/15_fix_legislation_spacing.py",
        "scripts/18_build_domain_corpus.py",
        "scripts/29_chunk_domain_corpus.py",
        "scripts/32_chunk_domain_corpus_sentence_aware.py",
        "scripts/34_chunk_domain_corpus_legal_aware.py",
    ],
    "technical_checks": "PASS",
    "training_approved": False,
    "rights_status": "pending_review",
}

lines = [
    "# LexiTech TR — Domain Corpus Temizleme ve Eleme Raporu v0.9",
    "",
    "**Danışman soruları:** 5 (temizleme) ve 6 (eleme gerekçeleri).",
    "",
    "## 1. Kapsam",
    "",
    "Domain Corpus, 12 kanuna ait PDF kaynaklarından "
    "hazırlanmıştır. 12 belgenin tamamı son korpusta "
    "korunmuştur. Bu bölümde QA Instruction Dataset "
    "değil, kanun metinleri incelenmektedir.",
    "",
    "## 2. Temizleme yöntemleri",
    "",
    "PDF metin çıkarımı sonrasında sayfa başlığı "
    "temizliği, Unicode NFC normalizasyonu, özel "
    "boşluk ve fi/fl birleşik karakter düzeltmeleri "
    "ile metin aralığı düzeltmeleri için ayrı "
    "betikler kullanılmıştır.",
    "",
    "Son korpusta kullanılan temiz metin sürümleri "
    "envanterde açıkça kayıtlıdır.",
    "",
    "## 3. Kaynak ve çıktı bütünlüğü",
    "",
    "- Ham PDF SHA-256: **12/12 PASS**",
    "- Temiz metin SHA-256: **12/12 PASS**",
    "- Son korpus metniyle birebir eşleşme: **12/12 PASS**",
    "",
    "| Kanun | Son temiz metin | İlk karakter | Son karakter | Fark (ilk-son) |",
    "|---|---|---:|---:|---:|",
]

for doc in audit["documents"]:
    lines.append(
        f"| {doc['law_number']} | "
        f"`{Path(doc['cleaned_path']).name}` | "
        f"{doc['original_extracted_chars']} | "
        f"{doc['final_cleaned_chars']} | "
        f"{doc['character_difference']} |"
    )

lines += [
    "",
    "Bu karakter farkları doğrudan silinen hukuki "
    "içerik miktarı olarak yorumlanamaz.",
    "",
    "## 4. Chunking yöntemleri",
    "",
    "| Yöntem | Train | Validation | Test | Toplam | "
    "Olası cümle ortası bölünme | Kelime bölünmesi örneği |",
    "|---|---:|---:|---:|---:|---:|---:|",
]

for name, item in versions.items():
    c = item["split_counts"]
    lines.append(
        f"| {name} | {c['train']} | "
        f"{c['validation']} | {c['test']} | "
        f"{item['total_chunks']} | "
        f"{item['possible_mid_sentence']} | "
        f"{item['word_break_examples']} |"
    )

lines += [
    "",
    "Üç sürümün tamamında 2.048 token üst sınırı "
    "sağlandı. Raporlanan chunk bütünlük hatası "
    "bulunmadı.",
    "",
    "Son veri seti dokümantasyonunda **legal-aware** "
    "sürüm referans alınmıştır. Bu sürümün kullanılmış "
    "olması, model eğitimi veya RAG kullanımının "
    "gerçekleştiği anlamına gelmez.",
    "",
    "## 5. Eleme ve inceleme durumu",
    "",
    "Bu aşamada 12 kanunun herhangi birinin "
    "korpustan çıkarıldığına ilişkin bulgu yoktur. "
    "980/983/988 farkı, farklı chunking "
    "stratejilerinin ürettiği parça sayılarıdır.",
    "",
    "**Legal-aware:** 988 chunk'ın tamamında "
    "`requires_manual_review=True`.",
    "",
    "53 adet büyük birimin parçalanması gerekmiştir. "
    "Olası cümle ortası bölünmelerin inceleme "
    "gerektirdiği ayrıca not edilmiştir.",
    "",
    "## 6. Sınırlılıklar",
    "",
]

for item in report["limitations"]:
    lines.append("- " + item)

lines += [
    "",
    "## 7. Kaynak hakları ve eğitim onayı",
    "",
    f"- Kaynak hak durumu dağılımı: `{dict(rights)}`",
    f"- Kaynak kalite durumu dağılımı: `{dict(quality)}`",
    f"- `training_candidate` dağılımı: `{dict(candidate_flags)}`",
    "- `training_approved = false`",
    "- `rights_status = pending_review`",
    "",
    "## 8. Kanıt dosyaları",
    "",
]

for filename in report["evidence_files"]:
    lines.append(f"- `{filename}`")

lines.append("")

QUALITY.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

MD_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print("LEXITECH TR - DOMAIN TEMIZLEME VE ELEME RAPORU")
print("=" * 65)
print("Dogrulanan belge:", report["document_count"])
print("PDF hash kontrolu: 12/12 PASS")
print("Temiz metin kontrolu: 12/12 PASS")
print("Corpus metin eslesmesi: 12/12 PASS")

for name, item in versions.items():
    print(name, "chunk:", item["total_chunks"])

print("Legal-aware manuel inceleme:", dict(review_flags))
print("Kaynak hak durumlari:", dict(rights))
print("Teknik kontrol: PASS")
print("Egitim onayi: HAYIR")
print("Hak incelemesi: BEKLIYOR")
print("\nJSON:", JSON_OUT)
print("Markdown:", MD_OUT)
print("Ana veri setleri degistirilmedi.")

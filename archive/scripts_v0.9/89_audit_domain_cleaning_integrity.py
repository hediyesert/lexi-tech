import csv
import hashlib
import json
from pathlib import Path

INVENTORY = Path("reports/sources/legislation_documents.csv")
CORPUS = Path("data/final/domain_corpus_v0.9.jsonl")

JSON_OUT = Path(
    "reports/quality/domain_cleaning_integrity_v0.9.json"
)
MD_OUT = Path(
    "reports/quality/domain_cleaning_integrity_v0.9.md"
)

if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit(
        "Rapor zaten mevcut. Üzerine yazılmadı."
    )

def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()

with INVENTORY.open(
    encoding="utf-8-sig",
    newline=""
) as f:
    inventory = list(csv.DictReader(f))

with CORPUS.open(encoding="utf-8") as f:
    corpus = [
        json.loads(line)
        for line in f
        if line.strip()
    ]

if len(inventory) != 12 or len(corpus) != 12:
    raise ValueError("12 envanter ve 12 corpus belgesi bekleniyor.")

by_document = {}

for record in corpus:
    document_id = str(record["document_id"])

    if document_id in by_document:
        raise ValueError(
            f"Tekrarlı corpus document_id: {document_id}"
        )

    by_document[document_id] = record

results = []
errors = []

for item in inventory:
    document_id = str(item["document_id"])
    law_number = str(item["law_number"])

    raw_path = Path(item["raw_path"])
    clean_path = Path(item["cleaned_path"])

    if not raw_path.is_file():
        errors.append(f"{law_number}: PDF bulunamadi")
        continue

    if not clean_path.is_file():
        errors.append(f"{law_number}: temiz metin bulunamadi")
        continue

    if document_id not in by_document:
        errors.append(f"{law_number}: corpus belgesi bulunamadi")
        continue

    record = by_document[document_id]

    raw_hash = sha256_file(raw_path)
    clean_hash = sha256_file(clean_path)

    raw_hash_pass = (
        raw_hash == item["raw_sha256"].strip().lower()
    )
    clean_hash_pass = (
        clean_hash == item["cleaned_sha256"].strip().lower()
    )

    cleaned_text = clean_path.read_text(encoding="utf-8")
    corpus_text = record["text"]

    text_equal = corpus_text == cleaned_text

    corpus_text_hash = hashlib.sha256(
        corpus_text.encode("utf-8")
    ).hexdigest()

    corpus_hash_pass = (
        corpus_text_hash == clean_hash
        and record["text_sha256"].lower() == clean_hash
    )

    char_count_pass = (
        record["char_count"] == len(corpus_text)
    )

    law_number_pass = (
        str(record["law_number"]) == law_number
    )

    original_path = (
        clean_path.parent
        / f"{raw_path.stem}.txt"
    )

    original_chars = None

    if original_path.is_file():
        original_chars = len(
            original_path.read_text(encoding="utf-8")
        )

    final_chars = len(cleaned_text)

    result = {
        "document_id": document_id,
        "law_number": law_number,
        "law_name": item["law_name"],
        "raw_path": str(raw_path),
        "cleaned_path": str(clean_path),
        "original_extracted_chars": original_chars,
        "final_cleaned_chars": final_chars,
        "character_difference": (
            original_chars - final_chars
            if original_chars is not None
            else None
        ),
        "raw_sha256_pass": raw_hash_pass,
        "cleaned_sha256_pass": clean_hash_pass,
        "corpus_text_exact_match": text_equal,
        "corpus_text_sha256_pass": corpus_hash_pass,
        "char_count_pass": char_count_pass,
        "law_number_pass": law_number_pass,
        "rights_status": item["rights_status"],
        "quality_status": item["quality_status"],
    }

    results.append(result)

    for field in (
        "raw_sha256_pass",
        "cleaned_sha256_pass",
        "corpus_text_exact_match",
        "corpus_text_sha256_pass",
        "char_count_pass",
        "law_number_pass",
    ):
        if not result[field]:
            errors.append(f"{law_number}: {field}")

if len(results) != 12:
    errors.append(
        f"Islenen belge sayisi {len(results)}, beklenen 12"
    )

report = {
    "project": "LexiTech TR",
    "version": "v0.9",
    "scope": "domain_cleaning_source_integrity",
    "documents_expected": 12,
    "documents_checked": len(results),
    "documents": results,
    "error_count": len(errors),
    "errors": errors,
    "status": "PASS" if not errors else "FAIL",
    "training_approved": False,
    "limitations": [
        "SHA-256 eşleşmesi hukuki doğruluk kanıtı değildir.",
        "Karakter azalması hukuki içerik kaybını dışlamaz.",
        "PDF'den çıkarma kalitesi ayrıca incelenmelidir.",
        "Kanun sürümleri ve güncellik ayrıca doğrulanmalıdır.",
        "Bağımsız hukuki inceleme tamamlanmamıştır.",
        "Bu rapor eğitim izni vermez.",
    ],
}

lines = [
    "# LexiTech TR — Domain Corpus Temizleme Bütünlüğü v0.9",
    "",
    "## Kaynak ve metin doğrulaması",
    "",
    "| Kanun | İlk metin karakteri | Son karakter | Fark | PDF hash | Metin eşleşmesi |",
    "|---|---:|---:|---:|---|---|",
]

for r in results:
    first = r["original_extracted_chars"]
    diff = r["character_difference"]

    lines.append(
        f"| {r['law_number']} | "
        f"{first if first is not None else 'YOK'} | "
        f"{r['final_cleaned_chars']} | "
        f"{diff if diff is not None else 'YOK'} | "
        f"{'PASS' if r['raw_sha256_pass'] else 'FAIL'} | "
        f"{'PASS' if r['corpus_text_exact_match'] else 'FAIL'} |"
    )

lines += [
    "",
    f"**Genel sonuç:** {report['status']}",
    "",
    "## Son korpusta kullanılan metinler",
    "",
]

for r in results:
    lines.append(
        f"- {r['law_number']}: `{r['cleaned_path']}`"
    )

lines += [
    "",
    "## Sınırlılıklar",
    "",
]

for limitation in report["limitations"]:
    lines.append("- " + limitation)

lines += [
    "",
    "**Eğitim onayı:** Verilmedi.",
    "",
]

if errors:
    print("LEXITECH TR - DOMAIN BUTUNLUK KONTROLU")
    print("=" * 60)

    for error in errors:
        print("HATA:", error)

    raise SystemExit(
        "FAIL: Rapor olusturulmadi; kaynak veriler degistirilmedi."
    )

JSON_OUT.parent.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

MD_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print("LEXITECH TR - DOMAIN TEMIZLEME BUTUNLUK RAPORU")
print("=" * 65)

for r in results:
    print(
        f"Kanun {r['law_number']}: "
        f"ilk={r['original_extracted_chars']}, "
        f"son={r['final_cleaned_chars']}, "
        f"fark={r['character_difference']}, "
        f"PDF_SHA256=PASS, "
        f"CORPUS_TEXT=PASS"
    )

print("\nDogrulanan kanun:", len(results))
print("Ham PDF SHA-256: 12/12 PASS")
print("Temiz metin SHA-256: 12/12 PASS")
print("Corpus metin eslesmesi: 12/12 PASS")
print("Metadata kontrolleri: PASS")
print("Genel sonuc:", report["status"])
print("Egitim onayi: HAYIR")

print("\nJSON:", JSON_OUT)
print("Markdown:", MD_OUT)
print("Hicbir kaynak veri dosyasi degistirilmedi.")

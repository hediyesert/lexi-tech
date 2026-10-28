import csv
import json
import re
import hashlib
from pathlib import Path

INPUT = Path("data/final/domain_corpus_v0.9_tokenized.jsonl")
OUTPUT = Path("reports/quality/domain_section_plan_v0.9.csv")

# Önceki Terminal denetimlerinde tespit edilen başlıklar.
UNINCORPORATED = {
    "2709": "18/10/1982 TARİHLİ VE 2709 SAYILI KANUNA İŞLENEMEYEN",
    "4721": "22/11/2001 TARİHLİ VE 4721 SAYILI KANUNA İŞLENEMEYEN",
    "6098": "6098 SAYILI KANUNA İŞLENEMEYEN",
    "5237": "5237 SAYILI KANUNA İŞLENEMEYEN",
    "5271": "5271 SAYILI KANUNA İŞLENEMEYEN",
    "2577": "6/1/1982 TARİHLİ VE 2577 SAYILI KANUNA İŞLENEMEYEN",
    "213": "4/1/1961 TARİHLİ VE 213 SAYILI ANA KANUNA İŞLENEMEYEN",
    "2004": "İŞLENEMEYEN HÜKÜMLER",
    "5510": "31/5/2006 TARİHLİ VE 5510 SAYILI KANUNA İŞLENEMEYEN",
}

with INPUT.open(encoding="utf-8") as f:
    documents = [
        json.loads(line)
        for line in f
        if line.strip()
    ]

if len(documents) != 12:
    raise ValueError("12 kanun bekleniyordu.")

rows = []

print("LEXITECH TR - GÜVENLİ BÖLÜMLEME PLANI")
print("=" * 60)

for doc in documents:
    number = str(doc["law_number"])
    text = doc["text"]

    lines = text.splitlines(keepends=True)

    starts = []
    offset = 0

    for line in lines:
        starts.append(offset)
        offset += len(line)

    if offset != len(text):
        raise ValueError(f"Satır bütünlüğü hatası: {number}")

    boundaries = [(0, "main_law", 1)]

    if number in UNINCORPORATED:
        marker = UNINCORPORATED[number].casefold()

        matches = [
            i for i, line in enumerate(lines)
            if marker in line.casefold()
        ]

        if len(matches) != 1:
            raise ValueError(
                f"{number}: işlenemeyen hükümler başlığı "
                f"{len(matches)} kez bulundu."
            )

        i = matches[0]
        boundaries.append(
            (starts[i], "unincorporated", i + 1)
        )

    # Tablo başlığını yalnızca ilgili kanun numarasıyla
    # başlayan gerçek üst başlıkta ara.
    pattern = re.compile(
        rf"^\s*{re.escape(number)}\s+SAYILI\s+KANUNA"
        rf"\s+EK\s+VE\s+DEĞİŞİKLİK\s+GETİREN",
        re.IGNORECASE
    )

    table_matches = [
        i for i, line in enumerate(lines)
        if pattern.search(line)
    ]

    if not table_matches:
        raise ValueError(
            f"{number}: değişiklik tablosu başlığı bulunamadı."
        )

    # Bazı kanunlarda birden fazla tablo başlığı bulunur.
    # İlkini başlangıç kabul et; sonraki tablolar içerikte korunur.
    table_i = table_matches[0]

    boundaries.append(
        (starts[table_i], "amendment_table", table_i + 1)
    )

    boundaries.sort()

    if len({b[0] for b in boundaries}) != len(boundaries):
        raise ValueError(f"Çakışan bölüm sınırı: {number}")

    reconstructed = []

    print(f"\n{number} - {doc['title']}")

    for j, (start, kind, line_no) in enumerate(boundaries):
        end = (
            boundaries[j + 1][0]
            if j + 1 < len(boundaries)
            else len(text)
        )

        if end <= start:
            raise ValueError(f"Geçersiz bölüm: {number}")

        section_text = text[start:end]
        reconstructed.append(section_text)

        rows.append({
            "law_number": number,
            "document_id": doc["document_id"],
            "section_type": kind,
            "start_char": start,
            "end_char": end,
            "start_line": line_no,
            "char_count": len(section_text),
            "section_sha256": hashlib.sha256(
                section_text.encode("utf-8")
            ).hexdigest()
        })

        print(
            f"  {kind}: satır {line_no}, "
            f"{len(section_text):,} karakter"
        )

    if "".join(reconstructed) != text:
        raise ValueError(f"Metin kaybı: {number}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

print("\nGENEL SONUÇ")
print("-" * 60)
print("Kanun sayısı:", len(documents))
print("Oluşturulan bölüm planı kaydı:", len(rows))
print("Metin kaybı:", 0)
print("Rapor:", OUTPUT)
print("Henüz chunk oluşturulmadı.")

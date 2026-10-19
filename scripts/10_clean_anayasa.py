import re
from pathlib import Path

source = Path("data/extracted/legislation/anayasa.txt")
target = Path("data/cleaned/legislation/anayasa.txt")

lines = source.read_text(encoding="utf-8").splitlines()

clean_lines = []
removed_pages = []
i = 0

while i < len(lines):
    current = lines[i].strip()

    if current == "19.10.2026 20:37" and i + 1 < len(lines):
        next_line = lines[i + 1].strip()

        match = re.match(r"Sayfa\s+(\d+)\s*/\s*67", next_line)

        if match and "mevzuat.gov.tr" in next_line:
            removed_pages.append(int(match.group(1)))
            i += 2
            continue

    clean_lines.append(lines[i])
    i += 1

expected_pages = list(range(1, 68))

if removed_pages != expected_pages:
    print("Bulunan sayfalar:", removed_pages)
    raise ValueError("Sayfa başlıkları eksik veya sıralaması hatalı.")

target.parent.mkdir(parents=True, exist_ok=True)

clean_text = "\n".join(clean_lines)
target.write_text(clean_text, encoding="utf-8")

print("Temizleme başarılı!")
print("Kaldırılan sayfa başlığı:", len(removed_pages))
print("Temiz metin karakter sayısı:", len(clean_text))
print("Kaydedilen dosya:", target)

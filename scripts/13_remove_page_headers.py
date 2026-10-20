import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
expected_count = int(sys.argv[3])

lines = source.read_text(encoding="utf-8").splitlines()

clean_lines = []
removed_pages = []
i = 0

date_pattern = r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}(?:\d{4})?"
page_pattern = r"^Sayfa\s+(\d+)\s*/\s*(\d+)"

while i < len(lines):
    if i + 1 < len(lines):
        current = lines[i].strip()
        next_line = lines[i + 1].strip()

        date_found = re.fullmatch(date_pattern, current)
        page_found = re.match(page_pattern, next_line)

        if date_found and page_found:
            page_number = int(page_found.group(1))
            total_pages = int(page_found.group(2))

            if (
                total_pages == expected_count
                and "mevzuat.gov.tr" in next_line
            ):
                removed_pages.append(page_number)
                i += 2
                continue

    clean_lines.append(lines[i])
    i += 1

expected_pages = list(range(1, expected_count + 1))

if removed_pages != expected_pages:
    raise ValueError(
        f"Sayfa başlıkları doğrulanamadı: {removed_pages}"
    )

target.parent.mkdir(parents=True, exist_ok=True)

clean_text = "\n".join(clean_lines)
target.write_text(clean_text, encoding="utf-8")

print("Temizleme başarılı!")
print("Kaldırılan sayfa başlığı:", len(removed_pages))
print("Önceki karakter sayısı:", len("\n".join(lines)))
print("Yeni karakter sayısı:", len(clean_text))
print("Kaydedilen dosya:", target)

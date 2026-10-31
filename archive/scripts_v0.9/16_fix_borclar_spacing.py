import re
from pathlib import Path

source = Path(
    "data/cleaned/legislation/borclar_kanunu_normalized.txt"
)
target = Path(
    "data/cleaned/legislation/borclar_kanunu_spacing_fixed.txt"
)

text = source.read_text(encoding="utf-8")

pattern = (
    r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,} "
    r"[ğĞ][A-Za-zÇĞİÖŞÜçğıöşü]+"
)

matches = re.findall(pattern, text)

print("Bulunan eşleşme:", len(matches))
print("Farklı ifade:", len(set(matches)))

# Beklenen sayıları kontrol et
if len(matches) != 89 or len(set(matches)) != 73:
    raise ValueError(
        "Beklenmeyen eşleşme sayısı! "
        "Dosya değiştirilmedi."
    )

# Yalnızca doğruladığımız boşluk örüntüsünü düzelt
fixed_text = re.sub(
    pattern,
    lambda match: match.group().replace(" ", "", 1),
    text
)

remaining = re.findall(pattern, fixed_text)

if remaining:
    raise ValueError("Düzeltilemeyen eşleşmeler var!")

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(fixed_text, encoding="utf-8")

print("\nDüzeltme başarılı!")
print("Düzeltilen eşleşme:", len(matches))
print("Kalan eşleşme:", len(remaining))
print("Önceki karakter sayısı:", len(text))
print("Yeni karakter sayısı:", len(fixed_text))
print("Kaydedilen dosya:", target)

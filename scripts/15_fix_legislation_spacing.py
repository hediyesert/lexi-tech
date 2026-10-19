import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])

text = source.read_text(encoding="utf-8")

pattern = (
    r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,} "
    r"[ğĞ][A-Za-zÇĞİÖŞÜçğıöşü]+"
)

matches = re.findall(pattern, text)

print("Bulunan eşleşme:", len(matches))
print("Farklı ifade:", len(set(matches)))

if len(matches) != 120 or len(set(matches)) != 73:
    raise ValueError(
        "Beklenmeyen eşleşme sayısı! İşlem durduruldu."
    )

def fix_match(match):
    return match.group().replace(" ", "", 1)

fixed_text = re.sub(pattern, fix_match, text)

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(fixed_text, encoding="utf-8")

print("\nDüzeltme başarılı!")
print("Düzeltilen eşleşme:", len(matches))
print("Kalan eşleşme:", len(re.findall(pattern, fixed_text)))
print("Önceki karakter sayısı:", len(text))
print("Yeni karakter sayısı:", len(fixed_text))
print("Kaydedilen dosya:", target)

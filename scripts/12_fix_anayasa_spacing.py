import re
from pathlib import Path

source = Path("data/cleaned/legislation/anayasa_reviewed.txt")
target = Path("data/cleaned/legislation/anayasa_spacing_fixed.txt")

text = source.read_text(encoding="utf-8")

pattern = (
    r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,} "
    r"[ğĞ][A-Za-zÇĞİÖŞÜçğıöşü]+"
)

matches = list(re.finditer(pattern, text))

print("Bulunan eşleşme:", len(matches))

if len(matches) != 66:
    raise ValueError(
        "Beklenen 66 eşleşme bulunamadı. İşlem durduruldu."
    )

def fix_match(match):
    wrong = match.group()
    return wrong.replace(" ", "", 1)

fixed_text = re.sub(pattern, fix_match, text)

target.write_text(fixed_text, encoding="utf-8")

print("Düzeltme başarılı!")
print("Düzeltilen eşleşme:", len(matches))
print("Kalan eşleşme:", len(re.findall(pattern, fixed_text)))
print("Önceki karakter sayısı:", len(text))
print("Yeni karakter sayısı:", len(fixed_text))
print("Kaydedilen dosya:", target)

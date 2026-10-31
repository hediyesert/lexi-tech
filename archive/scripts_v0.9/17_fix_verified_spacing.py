import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
expected_count = int(sys.argv[3])
expected_unique = int(sys.argv[4])

text = source.read_text(encoding="utf-8")

pattern = (
    r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,} "
    r"[ğĞ][A-Za-zÇĞİÖŞÜçğıöşü]+"
)

matches = re.findall(pattern, text)

print("Bulunan eşleşme:", len(matches))
print("Farklı ifade:", len(set(matches)))

if len(matches) != expected_count:
    raise ValueError("Eşleşme sayısı beklenenden farklı!")

if len(set(matches)) != expected_unique:
    raise ValueError("Farklı ifade sayısı beklenenden farklı!")

fixed_text = re.sub(
    pattern,
    lambda m: m.group().replace(" ", "", 1),
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

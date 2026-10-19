from pathlib import Path
import unicodedata

source = Path("data/cleaned/legislation/anayasa.txt")
target = Path("data/cleaned/legislation/anayasa_normalized.txt")

text = source.read_text(encoding="utf-8")

# Dönüşüm öncesi sayımlar
nbspaces = text.count("\u00a0")
fl_count = text.count("\ufb02")
fi_count = text.count("\ufb01")

# Güvenli karakter normalleştirme
text = unicodedata.normalize("NFC", text)
text = text.replace("\u00a0", " ")
text = text.replace("\ufb02", "fl")
text = text.replace("\ufb01", "fi")

target.write_text(text, encoding="utf-8")

print("Normalleştirme başarılı!")
print("Düzeltilen özel boşluk:", nbspaces)
print("Düzeltilen ﬂ karakteri:", fl_count)
print("Düzeltilen ﬁ karakteri:", fi_count)
print("Kalan özel boşluk:", text.count("\u00a0"))
print("Kalan birleşik karakter:", text.count("\ufb02") + text.count("\ufb01"))
print("Yeni karakter sayısı:", len(text))
print("Kaydedilen dosya:", target)

import sys
import unicodedata
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])

text = source.read_text(encoding="utf-8")

nbsp_count = text.count("\u00a0")
fl_count = text.count("\ufb02")
fi_count = text.count("\ufb01")

text = unicodedata.normalize("NFC", text)
text = text.replace("\u00a0", " ")
text = text.replace("\ufb02", "fl")
text = text.replace("\ufb01", "fi")

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding="utf-8")

print("Normalleştirme başarılı!")
print("Düzeltilen özel boşluk:", nbsp_count)
print("Düzeltilen ﬂ karakteri:", fl_count)
print("Düzeltilen ﬁ karakteri:", fi_count)
print("Kalan özel boşluk:", text.count("\u00a0"))
print("Yeni karakter sayısı:", len(text))
print("Kaydedilen dosya:", target)
